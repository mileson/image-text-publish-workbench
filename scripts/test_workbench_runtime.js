'use strict';
// Exercise the real event/controller code with deterministic DOM/storage boundaries.
// This is a logic test, not browser rendering or IndexedDB compatibility evidence.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto').webcrypto;
const C=require('../assets/workbench-core.js');
class Element {
  constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.className='';this.style={setProperty(){}};this.value='';this.hidden=false;this.disabled=false;this.listeners={};this.attributes={};this.classList={toggle(){},add(){},remove(){}};}
  append(...items){for(const child of items){child.parent=this;this.children.push(child);}}
  appendChild(child){this.append(child);}
  replaceChildren(...items){this.children=[];this.append(...items);}
  setAttribute(key,value){this.attributes[key]=value;}
  removeAttribute(key){delete this.attributes[key];}
  insertAdjacentHTML(){}
  addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  querySelectorAll(selector){const all=[];const visit=node=>{for(const child of node.children){if(selector==='[data-title-id]'?child.dataset.titleId!==undefined:child.tag===selector)all.push(child);visit(child);}};visit(this);return all;}
  closest(){let item=this;while(item&&!item.className.split(' ').includes('title-card'))item=item.parent;return item;}
  click(){if(!this.disabled)this.onclick?.({});}
  remove(){}
  select(){}
  showModal(){this.open=true;}
  close(){this.open=false;}
}
async function main(){
  const DATA={document_id:'runtime-fixture',input_fingerprint:'fixture',topic:'运行态测试',platform:'xiaohongshu',
    selected_title_id:'t1',selected_body_id:'b1',selected_cover_id:'c1',
    titles:[{id:'t1',label:'一',text:'初始标题'},{id:'t2',label:'二',text:'另一个标题'}],
    body_variants:[{id:'b1',label:'一',text:'正文一'},{id:'b2',label:'二',text:'正文二'}],
    tags:[{name:'话题一',selected:true,reason:'内容相关'},{name:'话题二',selected:false,reason:'内容相关'}],
    limits:{title:16,body:1000,tags:1,max_upload_bytes:1048576},
    covers:[{id:'c1',label:'封面',source:'registered',path:'/cover.png',width:30,height:40,data_url:'data:image/png;base64,fixture'}],photos:[]};
  const nodes=new Map();const get=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id);};
  const document={getElementById:get,createElement:tag=>new Element(tag),body:new Element('body')};
  let openRequest, pendingRead, writes=[];let timerId=0;const timers=new Map();
  const db={close(){},transaction(store,mode){const tx={};tx.objectStore=()=>({get(){const request={};pendingRead={tx,request};return request;},put(record){writes.push(record);Promise.resolve().then(()=>tx.oncomplete());}});return tx;}};
  const indexedDB={open(){openRequest={result:db};return openRequest;}};
  class Reader {readAsDataURL(blob){blob.arrayBuffer().then(bytes=>{this.result='data:'+blob.type+';base64,'+Buffer.from(bytes).toString('base64');this.onload();});}}
  class MockImage {constructor(){this.naturalWidth=30;this.naturalHeight=40;}set src(value){Promise.resolve().then(()=>this.onload());}}
  const navigator={clipboard:{async writeText(text){navigator.copied=text;}}};
  const window={crypto};
  const script=fs.readFileSync(path.join(__dirname,'../assets/workbench-app.js'),'utf8');
  const factory=new Function('DATA','WorkbenchCore','window','document','indexedDB','crypto','Image','FileReader','Blob','URL','navigator','setTimeout','clearTimeout',script+'\nreturn {get state(){return state},get assets(){return assets},uploadFiles,valid,persist,scheduleSave};');
  const api=factory(DATA,C,window,document,indexedDB,crypto,MockImage,Reader,Blob,{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},navigator,(fn,delay)=>{const id=++timerId;timers.set(id,{fn,delay});return id;},id=>timers.delete(id));
  // No user-facing mutation may run before the asynchronous saved draft has loaded.
  assert.equal(get('copyTitle').disabled,true);
  assert.equal(get('copyBody').disabled,true);
  const secondTitle=get('titles').children[1];
  assert.equal(secondTitle.querySelector('button').disabled,true);
  secondTitle.onclick();secondTitle.querySelector('button').click();
  get('bodyOptions').children[1].click();
  get('tags').children[0].click();
  get('bodyInput').value='读取完成前的输入';get('bodyInput').oninput();
  const before=JSON.stringify(api.state);
  api.scheduleSave();await api.persist();
  const file=bytes=>{const blob=new Blob([Uint8Array.from(bytes)],{type:'image/png'});Object.defineProperty(blob,'name',{value:'same-name.png'});return blob;};
  const header=[137,80,78,71,13,10,26,10];
  await api.uploadFiles([file([...header,1])],{kind:'cover',index:0});
  assert.equal(JSON.stringify(api.state),before);
  assert.equal(api.state.title_id,'t1');assert.equal(api.state.body_id,'b1');assert.equal(api.state.body_drafts.b1,'正文一');assert.deepEqual(api.state.tags,['话题一']);
  assert.equal(writes.length,0);
  assert.equal([...timers.values()].filter(t=>t.delay===200).length,0);
  // Resolve the existing saved record only after all premature input attempts.
  openRequest.onsuccess();await Promise.resolve();await Promise.resolve();
  const saved=C.defaults(DATA);saved.title_drafts.t1='从旧草稿恢复';
  pendingRead.request.result={state:saved,uploads:[]};pendingRead.request.onsuccess();pendingRead.tx.oncomplete();
  await window.workbenchReady;
  assert.equal(api.state.title_drafts.t1,'从旧草稿恢复');assert.equal(get('copyTitle').disabled,false);
  assert.equal(get('assetCaption').textContent,'封面 1');
  // Failed uploads leave the current image unchanged and the next attempt can succeed.
  await api.uploadFiles([file([1,2,3])],{kind:'cover',index:0});
  assert.equal(api.state.covers[0].id,'c1');
  const first=file([...header,1]),second=file([...header,2]);
  const firstOperation=api.uploadFiles([first],{kind:'cover',index:0});
  const secondOperation=api.uploadFiles([second],{kind:'cover',index:0});
  await Promise.all([firstOperation,secondOperation]);
  const hash=Buffer.from(await crypto.subtle.digest('SHA-256',await second.arrayBuffer())).toString('hex');
  assert.equal(api.assets[api.state.covers[0].id].sha256,hash);
  assert.equal(writes.at(-1).state.covers[0].id,api.state.covers[0].id);
  assert.equal(Object.values(api.assets).filter(a=>a.source==='uploaded').length,1);
  // A valid first append is persisted even if a later file in that batch fails.
  await api.uploadFiles([first,file([3,2,1])],null,true);
  assert.equal(api.state.photos.length,1);assert.equal(writes.at(-1).state.photos.length,1);
  // Copy/export must independently reject invalid topics, not just rely on restore/UI caps.
  api.state.tags=['话题一','话题二'];
  const selection=await window.getPublishReviewSelection();
  assert.equal(selection.tags_valid,false);assert.equal(selection.ready_for_handoff,false);assert.equal(api.valid(selection,true),false);
  navigator.copied=null;await get('copyAI').onclick();assert.equal(navigator.copied,null);
  get('copyBody').onclick();assert.equal(navigator.copied,null);
  api.state.tags=['话题一'];
  const draft=await window.getWorkbenchDraft();
  get('draftInput').files=[new Blob([JSON.stringify(draft)],{type:'application/json'})];
  get('draftInput').onchange();
  const last=file([...header,3]);
  api.uploadFiles([last],{kind:'cover',index:0});
  const afterImport=await window.getPublishReviewSelection();
  const lastHash=Buffer.from(await crypto.subtle.digest('SHA-256',await last.arrayBuffer())).toString('hex');
  assert.equal(afterImport.cover.sha256,lastHash);
  assert.equal(afterImport.images.length,2);
  console.log('runtime logic: initial-load guards, tag capacity, failed uploads, sequential replacement, partial-batch persistence passed');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
