'use client';
import {useEffect,useRef,useState} from 'react';
import {MapPin} from 'lucide-react';
export default function PropertyMap({latitude,longitude,label}:{latitude?:number|null;longitude?:number|null;label:string}){
 const ref=useRef<HTMLDivElement>(null);const [error,setError]=useState(false);const key=process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
 useEffect(()=>{if(!key||!latitude||!longitude||!ref.current)return;let cancelled=false;const w=window as any;
  const init=()=>{if(cancelled||!w.google?.maps||!ref.current)return;const map=new w.google.maps.Map(ref.current,{center:{lat:latitude,lng:longitude},zoom:15,disableDefaultUI:false});new w.google.maps.Marker({position:{lat:latitude,lng:longitude},map})};
  if(w.google?.maps){init();return()=>{cancelled=true}}const existing=document.querySelector('script[data-aashiyana-maps]') as HTMLScriptElement|null;
  if(existing){existing.addEventListener('load',init);return()=>{cancelled=true;existing.removeEventListener('load',init)}}
  const script=document.createElement('script');script.dataset.aashiyanaMaps='true';script.src=`https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=weekly`;script.async=true;script.onload=init;script.onerror=()=>setError(true);document.head.appendChild(script);return()=>{cancelled=true};
 },[key,latitude,longitude]);
 if(key&&latitude&&longitude&&!error)return <div ref={ref} style={{height:280,width:'100%',borderRadius:16}} aria-label={`Map showing ${label}`}/>;
 return <div className="map-fallback"><MapPin size={24}/><strong>{label}</strong><span>{key?'Map unavailable. Check the Google Maps API key and enabled APIs.':'Google Maps is not configured yet. Add NEXT_PUBLIC_GOOGLE_MAPS_API_KEY to enable interactive maps.'}</span></div>
}
