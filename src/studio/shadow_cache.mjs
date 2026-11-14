// Reuse shadow maps only when every visible caster/light input is unchanged.
export function createShadowCache(){
 const previous=new WeakMap();
 return function prepare(renderer,scene,camera){
  scene.updateMatrixWorld(true);const parts=[renderer.shadowMap.type,camera.layers?.mask],lights=[];let volatile=false;
  scene.traverseVisible(object=>{
   if(object.isLight&&object.castShadow&&object.shadow){
    lights.push(object);parts.push('light',object.uuid,...object.matrixWorld.elements,object.target?.uuid,...(object.target?.matrixWorld?.elements||[]),...(object.shadow.camera?.projectionMatrix?.elements||[]),object.shadow.mapSize.x,object.shadow.mapSize.y,object.shadow.map?.uuid||'');
   }
   if(!object.isMesh||!object.castShadow)return;
   if(object.isSkinnedMesh||object.morphTargetInfluences?.length||object.customDepthMaterial||object.customDistanceMaterial)volatile=true;
   const geometry=object.geometry;parts.push('mesh',object.uuid,object.layers?.mask,...object.matrixWorld.elements,geometry?.uuid,geometry?.attributes?.position?.version,geometry?.index?.version,object.instanceMatrix?.version,geometry?.drawRange?.start,geometry?.drawRange?.count);
   for(const material of Array.isArray(object.material)?object.material:[object.material]){
    parts.push(material?.uuid,material?.visible,material?.side,material?.shadowSide,material?.alphaTest,material?.opacity,material?.displacementScale,material?.displacementBias,material?.displacementMap?.version);
    if(material?.alphaTest>0||material?.alphaHash)parts.push(material.map?.uuid,material.map?.version,material.alphaMap?.uuid,material.alphaMap?.version);
   }
  });
  const key=parts.join('|'),dirty=volatile||previous.get(scene)!==key;
  previous.set(scene,key);renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=dirty;
  for(const light of lights){light.shadow.autoUpdate=false;light.shadow.needsUpdate=dirty;}
  return dirty;
 };
}
