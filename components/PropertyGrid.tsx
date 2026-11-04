import {Property} from '@/lib/data';import PropertyCard from './PropertyCard';
export default function PropertyGrid({items}:{items:Property[]}){return <div className="property-grid">{items.map(p=><PropertyCard key={p.id} property={p}/>)}</div>}
