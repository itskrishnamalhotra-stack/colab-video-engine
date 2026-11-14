// Persistent scene assemblies. Definitions are immutable; shot state changes
// transforms/actions on instances instead of constructing a different room.
export class EntityRegistry{
 constructor(){this.definitions=new Map();this.instances=new Map();this.serial=0;}
 define(name,{factory,required=[]}){
  if(this.definitions.has(name)||typeof factory!=='function')throw Error('Invalid/duplicate entity definition: '+name);
  this.definitions.set(name,Object.freeze({factory,required:Object.freeze([...required])}));return this;
 }
 async spawn(name,{id=name,parent=null,...options}={}){
  if(this.instances.has(id))throw Error('Duplicate entity instance: '+id);
  const def=this.definitions.get(name);if(!def)throw Error('Unknown entity: '+name);
  const value=await def.factory(options,this),root=value.root||value.group||value;
  if(!root?.isObject3D)throw Error('Entity needs an Object3D root: '+id);
  root.userData.entity={id,definition:name,serial:++this.serial};
  if(parent)parent.add(root);
  const record={id,definition:name,root,value,required:def.required,parts:new Map()};
  root.traverse(o=>{if(o.name){if(record.parts.has(o.name))throw Error('Duplicate named part '+id+'/'+o.name);record.parts.set(o.name,o);}});
  this.instances.set(id,record);this.assertEntity(record);return value;
 }
 get(id,part=null){const e=this.instances.get(id);if(!e)throw Error('Unknown entity instance: '+id);if(!part)return e.value;
  const value=e.parts.get(part);if(!value)throw Error('Missing entity part: '+id+'/'+part);return value;}
 assertEntity(e){
  for(const name of e.required){const part=e.parts.get(name);if(!part)throw Error('Missing required part: '+e.id+'/'+name);
   let node=part,attached=false;while(node){if(node===e.root){attached=true;break;}node=node.parent;}
   // Held objects may move to a named hand socket; their registry ownership
   // remains explicit and they must remain connected to the same scene graph.
   if(!attached){
    if(!part.userData.allowSocketTransfer||part.parent?.name!==part.userData.socket)throw Error('Detached required part: '+e.id+'/'+name);
    let ancestor=part;while(ancestor&&!ancestor.isScene)ancestor=ancestor.parent;
    let home=e.root;while(home&&!home.isScene)home=home.parent;
    if(!ancestor||ancestor!==home)throw Error('Transferred part left its scene: '+e.id+'/'+name);
   }
   if(!part.visible&&!part.userData.optionalVisibility)throw Error('Hidden required part: '+e.id+'/'+name);
  }
 }
 assertContinuity(){for(const e of this.instances.values())this.assertEntity(e);return true;}
 inventory(){return [...this.instances.values()].map(e=>({id:e.id,definition:e.definition,serial:e.root.userData.entity.serial,parts:[...e.parts.keys()],required:[...e.required]}));}
}

export function named(object,name){object.name=name;return object;}
export function transferToSocket(object,socket,{position=null,quaternion=null}={}){
 if(!socket?.isObject3D||!object?.isObject3D)throw Error('A real object and socket are required');
 socket.add(object);object.position.set(...(position||[0,0,0]));object.quaternion.identity();
 if(quaternion)object.quaternion.copy(quaternion);
 object.userData.allowSocketTransfer=true;object.userData.socket=socket.name;object.updateWorldMatrix(true,true);return object;
}
