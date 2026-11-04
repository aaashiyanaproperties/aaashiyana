'use client';
import { useEffect, useState } from 'react';
const read=<T,>(key:string,fallback:T):T=>{if(typeof window==='undefined')return fallback;try{return JSON.parse(localStorage.getItem(key)||'null')??fallback}catch{return fallback}};
export function useLocalState<T>(key:string,initial:T){const [value,setValue]=useState<T>(initial);const [ready,setReady]=useState(false);useEffect(()=>{setValue(read(key,initial));setReady(true)},[key]);useEffect(()=>{if(ready)localStorage.setItem(key,JSON.stringify(value))},[key,value,ready]);return [value,setValue] as const}
export function useDemoSession(){return useLocalState<{name:string,email:string,role:string}|null>('aashiyana-session',null)}
