"""Input validation, image metadata, and serialization for the image/text workbench."""
from __future__ import annotations
import base64
import hashlib
import io
import json
from pathlib import Path
from PIL import Image

SCHEMA = 'image-text-publish-workbench.input.v1'
SELECTION_SCHEMA = 'image-text-publish-workbench.selection.v1'
LIMITS = {'title': 16, 'body': 1000, 'tags': 10, 'max_upload_bytes': 33554432}
MIMES = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}
MAX_TOTAL_BYTES = 200 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def image_metadata(raw: bytes):
    with Image.open(io.BytesIO(raw)) as im:
        require(im.format in MIMES, '仅支持 JPEG、PNG、WebP 图片')
        width, height = im.size
        require(0 < width * height <= 36000000, '图片像素数需在 1 到 3600 万之间')
        require(not getattr(im, 'is_animated', False), '请使用静态图片')
        mime = MIMES[im.format]
        im.load()
        # Browser natural dimensions honor EXIF orientation. Mirror that metadata
        # convention without transposing/re-encoding pixels or changing raw bytes.
        if im.getexif().get(274, 1) in (5, 6, 7, 8):
            width, height = height, width
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'width': width, 'height': height, 'mime': mime}


def normalize(payload, *, check_files=True):
    require(isinstance(payload, dict), '输入必须是 JSON 对象')
    require(payload.get('schema_version') == SCHEMA, f'schema_version 必须为 {SCHEMA}')
    for key in ('document_id', 'topic'):
        require(isinstance(payload.get(key), str) and payload[key].strip(), f'{key} 不能为空')
    result = {**payload, 'platform': payload.get('platform', 'xiaohongshu')}
    require(isinstance(result['platform'], str) and result['platform'].strip(), 'platform 不能为空')
    result['limits'] = {**LIMITS, **payload.get('limits', {})}
    for key, value in result['limits'].items():
        require(key in LIMITS and type(value) is int and value > 0, f'limits.{key} 必须为正整数')
    require(result['limits']['max_upload_bytes'] <= MAX_TOTAL_BYTES, '单张上传预算不能超过 200 MiB')
    for key in ('titles', 'body_variants'):
        rows = payload.get(key)
        require(isinstance(rows, list) and rows, f'{key} 至少需要一个候选')
        ids = []
        for row in rows:
            require(isinstance(row, dict), f'{key} 候选必须为对象')
            for field in ('id', 'label', 'text'):
                require(isinstance(row.get(field), str) and (row[field].strip() or field == 'text'), f'{key}.{field} 无效')
            require(row['id'] not in ids, f'{key} 存在重复 id')
            ids.append(row['id'])
            if key == 'titles':
                require(len(row['text']) <= result['limits']['title'], f'标题超限：{row["id"]}')
            else:
                require(len(row['text']) <= result['limits']['body'], f'正文超限：{row["id"]}')
        selection_key = 'selected_title_id' if key == 'titles' else 'selected_body_id'
        result[selection_key] = payload.get(selection_key, ids[0])
        require(result[selection_key] in ids, f'{selection_key} 不在候选中')
    tags = payload.get('tags', [])
    require(isinstance(tags, list), 'tags 必须为数组')
    names = set()
    for tag in tags:
        require(isinstance(tag, dict), '话题必须为对象')
        name = tag.get('name')
        require(isinstance(name, str) and name and not any(c.isspace() or c == '#' for c in name), '话题不能含空白或 #')
        require(name not in names, f'重复话题：{name}')
        require(type(tag.get('selected')) is bool, '话题 selected 必须为布尔值')
        require(isinstance(tag.get('reason'), str) and tag['reason'].strip(), '话题需要 reason')
        require(tag.get('source_url') is None or isinstance(tag.get('source_url'), str), 'source_url 必须为字符串或 null')
        names.add(name)
    result['tags'] = tags
    require(sum(t['selected'] for t in tags) <= result['limits']['tags'], '默认话题数量超限')
    body = next(row['text'] for row in result['body_variants'] if row['id'] == result['selected_body_id'])
    tag_line = ' '.join('#' + tag['name'] for tag in tags if tag['selected'])
    composed = body.rstrip() + ('\n\n' + tag_line if tag_line else '')
    require(len(composed) <= result['limits']['body'], '默认正文与话题合计超限')
    asset_ids = set()
    total = 0
    for key, role in (('covers', 'cover'), ('photos', 'photo')):
        assets = payload.get(key, [])
        require(isinstance(assets, list), f'{key} 必须为数组')
        result[key] = []
        for asset in assets:
            require(isinstance(asset, dict), '图片必须为对象')
            require(isinstance(asset.get('id'), str) and asset['id'].strip() and asset['id'] not in asset_ids, '图片 id 必须非空且全局唯一')
            require(not asset['id'].startswith('upload-'), '图片 id 不能以 upload- 开头')
            require(isinstance(asset.get('label'), str) and asset['label'].strip(), '图片 label 不能为空')
            require(asset.get('role') == role, f'{key} 图片 role 必须为 {role}')
            require(isinstance(asset.get('path'), str) and Path(asset['path']).is_absolute(), '图片 path 必须为绝对路径')
            asset_ids.add(asset['id'])
            prepared = {key: value for key, value in asset.items() if key not in ('data_url', 'previewUrl')}
            if check_files:
                path = Path(asset['path']).resolve()
                require(path.is_file(), f'图片不存在：{path}')
                require(path.stat().st_size <= result['limits']['max_upload_bytes'], f'图片超过单张预算：{path.name}')
                raw = path.read_bytes()
                meta = image_metadata(raw)
                total += len(raw)
                require(total <= MAX_TOTAL_BYTES, '图片总量超过 200 MiB，请分批制作')
                if asset.get('sha256'):
                    require(asset['sha256'] == meta['sha256'], f'图片内容已改变：{path.name}')
                prepared.update(meta, path=str(path), fileName=path.name, source='registered', publishable=True)
                prepared['data_url'] = f'data:{meta["mime"]};base64,' + base64.b64encode(raw).decode('ascii')
            result[key].append(prepared)
    result['selected_cover_id'] = payload.get('selected_cover_id', result['covers'][0]['id'] if result['covers'] else None)
    require(result['selected_cover_id'] is None or result['selected_cover_id'] in [a['id'] for a in result['covers']], 'selected_cover_id 不在封面候选中')
    return result


def json_for_script(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def lean_payload(payload):
    return {**payload, **{key: [{k: v for k, v in a.items() if k != 'data_url'} for a in payload[key]] for key in ('covers', 'photos')}}
