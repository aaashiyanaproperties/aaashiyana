import { firebaseAuth } from './firebase';
const BASE=(process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api').replace(/\/$/,'');
export function hasDevSession(){if(typeof window==='undefined')return Boolean(process.env.NEXT_PUBLIC_DEV_AUTH_EMAIL);try{return Boolean(process.env.NEXT_PUBLIC_DEV_AUTH_EMAIL||JSON.parse(localStorage.getItem('aashiyana-session')||'null')?.email)}catch{return false}}
export class ApiError extends Error { constructor(public status:number,message:string){super(message)} }
export async function api<T>(path:string,init:RequestInit={}):Promise<T>{
  const token=await firebaseAuth?.currentUser?.getIdToken();
  const headers=new Headers(init.headers); if(init.body && !(init.body instanceof FormData)) headers.set('Content-Type','application/json'); if(token) headers.set('Authorization',`Bearer ${token}`);else if(process.env.NODE_ENV!=='production'&&hasDevSession()){let email=process.env.NEXT_PUBLIC_DEV_AUTH_EMAIL||'';try{email=email||JSON.parse(localStorage.getItem('aashiyana-session')||'null')?.email||''}catch{}if(email)headers.set('X-Dev-User',email)}
  const res=await fetch(`${BASE}${path}`,{...init,headers,cache:'no-store'});
  const data=await res.json().catch(()=>({detail:res.statusText})); if(!res.ok) throw new ApiError(res.status,data.detail||'Request failed'); return data as T;
}
export type ApiProperty={id:string;property_id:string;slug:string;title:string;description:string;transaction_type:string;property_type:string;status:string;city:string;state:string;locality:string;price:number;bedrooms:number;bathrooms:number;carpet_area:number|null;builtup_area:number|null;furnishing:string;parking:number;possession_status:string;latitude:number|null;longitude:number|null;floor_number:number|null;total_floors:number|null;images:string[];amenities:string[];rera_number:string|null;rera_verified:boolean;demo:boolean;created_at:string};
export async function searchProperties(filters:Record<string,string|number|boolean|undefined>={}){const q=new URLSearchParams();Object.entries(filters).forEach(([k,v])=>{if(v!==undefined&&v!==''&&v!==false)q.set(k,String(v))});return api<{items:ApiProperty[];total:number;page:number;pages:number}>(`/properties?${q}`)}
