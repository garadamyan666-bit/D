document.addEventListener('DOMContentLoaded',()=>{
  const image=document.getElementById('chartImage'),preview=document.getElementById('chartPreview'),button=document.getElementById('analyzeChart'),message=document.getElementById('chartMessage'),result=document.getElementById('chartResult');
  let dataUrl='';
  image.addEventListener('change',()=>{
    const file=image.files[0];dataUrl='';result.hidden=true;
    if(!file)return;
    if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>5*1024*1024){message.textContent='Ընտրեք մինչև 5 MB PNG, JPG կամ WEBP նկար։';image.value='';preview.hidden=true;return;}
    const reader=new FileReader();reader.onload=()=>{dataUrl=reader.result;preview.src=dataUrl;preview.hidden=false;message.textContent='Նկարը պատրաստ է վերլուծության։';};reader.readAsDataURL(file);
  });
  button.addEventListener('click',async()=>{
    if(!dataUrl){message.textContent='Նախ ընտրեք գրաֆիկի նկարը։';return;}
    button.disabled=true;result.hidden=true;message.textContent='AI-ը վերլուծում է նկարը…';
    try{const response=await fetch('/api/chart-analysis',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_data:dataUrl,symbol:document.getElementById('chartSymbol').value,timeframe:document.getElementById('chartTimeframe').value})});const body=await response.json();if(!response.ok)throw Error(body.detail||'Վերլուծությունը չստացվեց։');result.textContent=body.analysis;result.hidden=false;message.textContent='Պատրաստ է։ Նկարը կայքի բազայում չի պահպանվել։';}
    catch(error){message.textContent=error.message;}finally{button.disabled=false;}
  });
});
