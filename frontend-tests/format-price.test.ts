import {describe,expect,it} from 'vitest';
import {formatPrice} from '../lib/data';
describe('Indian property price formatting',()=>{
  it('formats lakh values in INR',()=>expect(formatPrice(4500000)).toBe('₹45 L'));
  it('formats crore values in INR',()=>expect(formatPrice(12500000)).toBe('₹1.25 Cr'));
  it('formats monthly rent',()=>expect(formatPrice(24500,'Rent')).toBe('₹24,500/mo'));
});
