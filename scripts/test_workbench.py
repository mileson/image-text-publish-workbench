#!/usr/bin/env python3
"""Serial, lightweight contract regression tests; no browser or server is started."""
import base64
import copy
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from workbench_lib import normalize, lean_payload, image_metadata, SCHEMA, SELECTION_SCHEMA
from build_workbench import build, ROOT
from materialize_selection import materialize


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='image-text-workbench-test-')
        self.root = Path(self.temp.name).resolve()
        self.image = self.root / 'source.png'
        Image.new('RGB', (30, 40), '#e54b6a').save(self.image)
        self.base = json.loads((ROOT / 'examples/workbench-input.json').read_text())
        self.base['covers'] = [{'id':'cover-a','label':'封面','path':str(self.image),'role':'cover'}]
        self.base['photos'] = [{'id':'photo-a','label':'内页','path':str(self.image),'role':'photo'}]

    def tearDown(self):
        self.temp.cleanup()

    def selection(self, uploaded=False):
        payload = normalize(self.base)
        images = []
        for original in payload['covers'] + payload['photos']:
            asset = copy.deepcopy(original)
            if uploaded:
                asset.update(path=None, source='uploaded', publishable=False, fileName='../../outside.png')
            else:
                asset.pop('data_url')
            images.append(asset)
        body = self.base['body_variants'][0]['text']
        return {'schema_version':SELECTION_SCHEMA, 'document_id':'test','topic':'测试', 'platform':'xiaohongshu',
                'title':self.base['titles'][0]['text'],'body':body,'tags':['城市散步'],
                'composed_body':body+'\n\n#城市散步','cover':images[0],'images':images,
                'limits':payload['limits'],'review_only':True}

    def test_minimal_empty_assets(self):
        payload = copy.deepcopy(self.base)
        payload['covers'], payload['photos'] = [], []
        normalized = normalize(payload)
        self.assertIsNone(normalized['selected_cover_id'])
        self.assertEqual(len(normalized['titles']), 1)

    def test_variable_variants(self):
        payload = copy.deepcopy(self.base)
        payload['titles'] = [{'id':str(i),'label':str(i),'text':'标题'+str(i)} for i in range(7)]
        payload['body_variants'] = [{'id':'one','label':'正文','text':'只有一份正文'}]
        normalized = normalize(payload)
        self.assertEqual(len(normalized['titles']),7)
        self.assertEqual(len(normalized['body_variants']),1)

    def test_build_round_trip_and_script_escape(self):
        payload = copy.deepcopy(self.base)
        payload['body_variants'][0]['text'] = '</script><script>alert(1)</script>'
        path = self.root/'input.json'
        path.write_text(json.dumps(payload))
        result = build(path,self.root/'workbench.html')
        html = Path(result['html']).read_text()
        injected = re.search(r'<script>const DATA=(.*?);</script>',html,re.S).group(1)
        self.assertNotIn('</script>',injected)
        self.assertEqual(json.loads(injected)['body_variants'][0]['text'],payload['body_variants'][0]['text'])
        normalized = json.loads(Path(result['input']).read_text())
        self.assertNotIn('data_url',normalized['covers'][0])
        self.assertEqual(normalize(normalized)['covers'][0]['sha256'],normalize(payload)['covers'][0]['sha256'])
        node = shutil.which('node')
        self.assertIsNotNone(node,'JavaScript syntax verification requires existing Node runtime')
        extracted = self.root/'check.js'
        extracted.write_text('\n'.join(re.findall(r'<script>(.*?)</script>',html,re.S)))
        subprocess.run([node,'--check',str(extracted)],check=True,capture_output=True)

    def test_duplicate_asset_ids_rejected(self):
        self.base['photos'][0]['id']='cover-a'
        with self.assertRaisesRegex(ValueError,'全局唯一'):
            normalize(self.base)

    def test_changed_registered_asset_rejected(self):
        selected=self.selection()
        Image.new('RGB',(30,40),'#000').save(self.image)
        with self.assertRaisesRegex(ValueError,'指纹'):
            materialize(selected,self.root/'out')
        self.assertFalse((self.root/'out').exists())

    def test_materialize_uploaded_bytes_and_names(self):
        selected=self.selection(uploaded=True)
        result=materialize(selected,self.root/'out')
        resolved=json.loads(Path(result['selection']).read_text())
        self.assertEqual(result['materialized_uploads'],2)
        for asset in resolved['images']:
            path=Path(asset['path'])
            self.assertEqual(path.parent,self.root/'out')
            self.assertNotIn('data_url',asset)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),asset['sha256'])
            self.assertTrue(asset['publishable'])
        materialize(selected,self.root/'out')

    def test_tampered_upload_rejected_before_any_write(self):
        selected=self.selection(uploaded=True)
        selected['images'][1]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'指纹'):
            materialize(selected,self.root/'out')
        self.assertFalse((self.root/'out').exists())

    def test_faked_original_path_rejected(self):
        selected=self.selection(uploaded=True)
        selected['images'][0]['path']='/fake/source.png'
        with self.assertRaisesRegex(ValueError,'推测'):
            materialize(selected,self.root/'out')

    def test_capacity_validation(self):
        self.base['limits']={'body':4}
        with self.assertRaisesRegex(ValueError,'超限'):
            normalize(self.base)

    def test_spoofed_valid_flags_not_trusted(self):
        selected=self.selection()
        selected.update(title='过'*17,title_valid=True,ready_for_handoff=True)
        with self.assertRaisesRegex(ValueError,'标题'):
            materialize(selected,self.root/'out')

    def test_mime_and_role_verified(self):
        selected=self.selection(uploaded=True)
        selected['images'][0]['data_url']=selected['images'][0]['data_url'].replace('image/png','image/jpeg')
        with self.assertRaisesRegex(ValueError,'格式'):
            materialize(selected,self.root/'out')

    def make_oriented_jpeg(self, orientation):
        path = self.root / f'phone-orientation-{orientation}.jpg'
        image = Image.new('RGB', (40, 30), '#e54b6a')
        exif = image.getexif()
        exif[274] = orientation
        image.save(path, format='JPEG', exif=exif)
        return path

    def test_exif_display_dimensions_do_not_change_original(self):
        for orientation in (1, 2, 3, 4, 5, 6, 7, 8):
            with self.subTest(orientation=orientation):
                path = self.make_oriented_jpeg(orientation)
                original = path.read_bytes()
                expected_size = (30, 40) if orientation in (5, 6, 7, 8) else (40, 30)
                metadata = image_metadata(original)
                self.assertEqual((metadata['width'], metadata['height']), expected_size)
                self.assertEqual(metadata['sha256'], hashlib.sha256(original).hexdigest())
                self.assertEqual(path.read_bytes(), original)
                with Image.open(path) as raw_image:
                    self.assertEqual(raw_image.size, (40, 30))
                    self.assertEqual(raw_image.getexif()[274], orientation)

    def test_materialize_phone_exif_6_and_8_preserves_bytes(self):
        for orientation in (6, 8):
            with self.subTest(orientation=orientation):
                path = self.make_oriented_jpeg(orientation)
                original = path.read_bytes()
                for group in ('covers', 'photos'):
                    self.base[group][0]['path'] = str(path)
                selected = self.selection(uploaded=True)
                # Model the browser's oriented natural dimensions explicitly,
                # independently of the Python metadata used to seed the fixture.
                for asset in selected['images']:
                    asset['width'], asset['height'] = 30, 40
                result = materialize(selected, self.root / f'out-{orientation}')
                resolved = json.loads(Path(result['selection']).read_text())
                for asset in resolved['images']:
                    self.assertEqual((asset['width'], asset['height']), (30, 40))
                    self.assertEqual(Path(asset['path']).read_bytes(), original)
                    self.assertEqual(asset['sha256'], hashlib.sha256(original).hexdigest())
                    with Image.open(asset['path']) as preserved:
                        self.assertEqual(preserved.size, (40, 30))
                        self.assertEqual(preserved.getexif()[274], orientation)

    def test_runtime_controller_boundaries(self):
        script = ROOT/'scripts/test_workbench_runtime.js'
        subprocess.run([shutil.which('node'),str(script)],check=True,text=True)

    def test_core_state_and_current_assets(self):
        script = ROOT/'scripts/test_workbench_core.js'
        subprocess.run([shutil.which('node'),str(script)],check=True,capture_output=True,text=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
