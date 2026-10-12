#!/usr/bin/env python3
"""Verify current publishing assets and persist browser uploads without inventing source paths."""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from workbench_lib import SELECTION_SCHEMA, LIMITS, MAX_TOTAL_BYTES, image_metadata, require


def materialize(selection, output_dir):
    require(isinstance(selection, dict) and selection.get('schema_version') == SELECTION_SCHEMA, '发布信息版本不匹配')
    require(selection.get('review_only') is True, '必须是本地评审发布信息')
    require(isinstance(selection.get('document_id'), str) and selection['document_id'], '缺少 document_id')
    limits = {**LIMITS, **selection.get('limits', {})}
    require(all(type(v) is int and v > 0 for v in limits.values()), '无效容量限制')
    title, body, tags = selection.get('title'), selection.get('body'), selection.get('tags')
    require(isinstance(title, str) and title.strip() and len(title) <= limits['title'], '标题为空或超限')
    require(isinstance(body, str) and isinstance(tags, list) and all(isinstance(t, str) and t and not any(c.isspace() or c == '#' for c in t) for t in tags), '正文或话题无效')
    require(len(set(tags)) == len(tags) and len(tags) <= limits['tags'], '话题重复或超限')
    composed = body.rstrip() + ('\n\n' + ' '.join('#' + t for t in tags) if tags else '')
    require(len(composed) <= limits['body'] and composed == selection.get('composed_body'), '正文合成内容不匹配或超限')
    images = selection.get('images')
    require(isinstance(images, list) and images, '缺少发布图片')
    prepared = []
    total = 0
    output_dir = Path(output_dir).resolve()
    for index, asset in enumerate(images):
        require(isinstance(asset, dict), '图片元信息无效')
        role = 'cover' if index == 0 else 'photo'
        require(asset.get('role') == role, '图片顺序需为封面后接内页')
        require(isinstance(asset.get('id'), str) and asset['id'], '图片缺少 id')
        require(re.fullmatch('[0-9a-f]{64}', asset.get('sha256', '')) is not None, '图片缺少有效 SHA-256')
        if asset.get('source') == 'uploaded':
            require(asset.get('path') is None, '浏览器上传图片不能携带推测的原始路径')
            match = re.fullmatch(r'data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)', asset.get('data_url', ''))
            require(match is not None, '上传图片缺少有效 data_url')
            require(len(match[2]) <= min(limits['max_upload_bytes'], MAX_TOTAL_BYTES) * 1.4, '上传图片编码过大')
            raw = base64.b64decode(match[2], validate=True)
            meta = image_metadata(raw)
            require(match[1] == meta['mime'], '上传图片格式与编码声明不符')
            extension = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}[meta['mime']]
            path = output_dir / f'{index:02d}-{role}-{meta["sha256"][:16]}{extension}'
        else:
            require(asset.get('source') == 'registered', '图片来源无效')
            require(isinstance(asset.get('path'), str) and Path(asset['path']).is_absolute(), '登记图片缺少绝对路径')
            path = Path(asset['path']).resolve()
            require(path.is_file(), f'登记图片不存在：{path}')
            require(path.stat().st_size <= min(limits['max_upload_bytes'], MAX_TOTAL_BYTES), '登记图片过大')
            raw = path.read_bytes()
            meta = image_metadata(raw)
        total += len(raw)
        require(total <= MAX_TOTAL_BYTES and len(raw) <= limits['max_upload_bytes'], '图片超出工作台容量预算')
        require(meta['sha256'] == asset['sha256'] and meta['size'] == asset.get('size'), '图片内容指纹不匹配')
        require(meta['width'] == asset.get('width') and meta['height'] == asset.get('height'), '图片尺寸不匹配')
        if asset.get('source') == 'uploaded' and path.exists():
            require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == meta['sha256'], '输出位置已有不同内容，停止覆盖')
        prepared.append((asset, raw, meta, path))
    require(isinstance(selection.get('cover'), dict) and selection['cover'].get('sha256') == images[0]['sha256'] and selection['cover'].get('id') == images[0]['id'], '封面与图片首项不一致')
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved = []
    for original, raw, meta, path in prepared:
        if original['source'] == 'uploaded' and not path.exists():
            with path.open('xb') as handle:
                handle.write(raw)
        clean = {k: v for k, v in original.items() if k != 'data_url'}
        clean.update(meta, path=str(path), fileName=path.name, source='registered', publishable=True)
        resolved.append(clean)
    result = {**selection, 'images': resolved, 'cover': resolved[0], 'ready_for_handoff': True, 'title_valid': True, 'body_valid': True, 'assets_valid': True, 'tags_valid': True}
    path = output_dir / 'publish-selection.resolved.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'ok': True, 'selection': str(path), 'images': len(resolved), 'materialized_uploads': sum(a['source'] == 'uploaded' for a in images), 'published': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = args.selection.read_text(encoding='utf-8')
        if not raw.lstrip().startswith('{'):
            raw = raw[raw.index('{'):]
        print(json.dumps(materialize(json.loads(raw), args.output_dir), ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
