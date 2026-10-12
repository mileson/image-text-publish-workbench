/* Pure state and publishing contract shared by the browser and Node regression tests. */
(function (root) {
  'use strict';
  const clone = value => JSON.parse(JSON.stringify(value));
  const count = value => Array.from(String(value)).length;
  function defaults(data) {
    const covers = data.covers.map(a => ({id:a.id, original_id:a.id}));
    while (covers.length < 3) covers.push({id:null, original_id:null});
    if (data.selected_cover_id === null && !covers.some(s => s.id === null)) covers.push({id:null,original_id:null});
    return {title_id:data.selected_title_id, body_id:data.selected_body_id,
      title_drafts:Object.fromEntries(data.titles.map(v => [v.id,v.text])),
      body_drafts:Object.fromEntries(data.body_variants.map(v => [v.id,v.text])),
      tags:data.tags.filter(t => t.selected).map(t => t.name), covers,
      selected_cover:Math.max(0,covers.findIndex(s => s.id === data.selected_cover_id)),
      photos:data.photos.map(a => ({id:a.id,original_id:a.id}))};
  }
  function restore(data, saved, assetIds) {
    const base = defaults(data);
    if (!saved || typeof saved !== 'object') return base;
    const validIds = new Set(assetIds);
    for (const [key,list] of [['title_drafts',data.titles],['body_drafts',data.body_variants]]) {
      for (const row of list) if (typeof saved[key]?.[row.id] === 'string') base[key][row.id] = saved[key][row.id];
    }
    if (data.titles.some(v => v.id === saved.title_id)) base.title_id = saved.title_id;
    if (data.body_variants.some(v => v.id === saved.body_id)) base.body_id = saved.body_id;
    if (Array.isArray(saved.tags)) base.tags = [...new Set(saved.tags)].filter(t => data.tags.some(v => v.name === t)).slice(0,data.limits.tags);
    for (const key of ['covers','photos']) {
      if (!Array.isArray(saved[key])) continue;
      const originalIds = new Set(data[key].map(a => a.id));
      base[key] = saved[key].filter(v => v && typeof v === 'object').map(v => ({
        id: validIds.has(v.id) ? v.id : null,
        original_id:originalIds.has(v.original_id) ? v.original_id : null,
        missing: Boolean(v.id && !validIds.has(v.id))
      }));
    }
    while (base.covers.length < 3) base.covers.push({id:null,original_id:null});
    if (Number.isInteger(saved.selected_cover) && saved.selected_cover >= 0 && saved.selected_cover < base.covers.length) base.selected_cover = saved.selected_cover;
    return base;
  }
  function compose(state) {
    return state.body_drafts[state.body_id].trimEnd() + (state.tags.length ? '\n\n' + state.tags.map(t=>'#'+t).join(' ') : '');
  }
  function selection(data, state, assets, includeData=true) {
    function serialize(slot, role) {
      if (!slot?.id || !assets[slot.id]) return null;
      const {data_url, blob, previewUrl, ...meta} = assets[slot.id];
      return {...meta,role,...(includeData && meta.source === 'uploaded' ? {data_url} : {})};
    }
    const cover = serialize(state.covers[state.selected_cover],'cover');
    const photos = state.photos.map(s => serialize(s,'photo'));
    const body = compose(state), title = state.title_drafts[state.title_id];
    const title_valid = Boolean(title.trim()) && count(title) <= data.limits.title;
    const body_valid = count(body) <= data.limits.body;
    const assets_valid = Boolean(cover) && photos.every(Boolean);
    const tags_valid = state.tags.length <= data.limits.tags && new Set(state.tags).size === state.tags.length && state.tags.every(t => data.tags.some(v => v.name === t));
    return {schema_version:'image-text-publish-workbench.selection.v1',document_id:data.document_id,
      topic:data.topic,platform:data.platform,title,body:state.body_drafts[state.body_id],tags:[...state.tags],
      composed_body:body,title_variant:state.title_id,body_variant:state.body_id,cover,
      images:[cover,...photos].filter(Boolean),title_valid,body_valid,assets_valid,tags_valid,
      body_count:count(body),limits:clone(data.limits),review_only:true,
      ready_for_handoff:title_valid && body_valid && assets_valid && tags_valid};
  }
  const api = {clone,count,defaults,restore,compose,selection};
  root.WorkbenchCore = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
