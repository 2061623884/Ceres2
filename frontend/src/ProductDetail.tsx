import { useEffect, useState } from 'react'
import { getProduct, productImageUrl, yuan, type Product } from './lib/saleGuide'

export default function ProductDetail({ skuId, onClose, onAdd, adding }: {
  skuId: string; onClose: () => void; onAdd: (skuId: string) => void; adding: boolean
}) {
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let current = true
    setProduct(null)
    setError(null)
    void getProduct(skuId).then(value => { if(current) setProduct(value) })
      .catch(error => { if(current) setError(error instanceof Error ? error.message : '商品读取失败') })
    return () => { current = false }
  }, [skuId])
  return <section role="dialog" aria-label="商品详情" className="absolute inset-0 z-40 flex flex-col overflow-y-auto bg-[#fcfbf8] p-5">
    <header className="mb-5 flex items-center justify-between"><h2 className="text-xl font-semibold">商品详情</h2><button onClick={onClose}>关闭</button></header>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {!product && !error && <p role="status">正在读取商品…</p>}
    {product && <>
      <img className="mb-5 aspect-square w-full rounded-3xl object-cover" src={productImageUrl(product.image_path)} alt={product.name_zh || product.name} />
      <h3 className="text-2xl font-semibold">{product.name_zh || product.name}</h3>
      <p className="mt-2 text-sm text-black/55">{product.brand} · {product.spec_quantity === null || product.spec_unit == null ? '规格未知' : `${product.spec_quantity}${product.spec_unit}`}</p>
      <p className="mt-4 text-xl font-semibold">{product.price_fen == null ? '当前价格未知' : yuan(product.price_fen)} / 销售包装</p>
      <p className="mt-2 text-sm">{product.sellable ? `模拟可售数量：${product.available_qty ?? '未知'}` : '当前不可售'}</p>
      <p className="mt-5 text-xs leading-5 text-black/50">价格与库存为模拟数据，售后适用规则见服务政策。</p>
      <button className="mt-6 rounded-full bg-[#171716] px-5 py-3 text-sm font-semibold text-white disabled:opacity-40" disabled={adding || !product.sellable} onClick={() => onAdd(product.sku_id)}>{adding ? '正在添加…' : '添加一件到购物车'}</button>
    </>}
  </section>
}
