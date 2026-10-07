import { useEffect, useState } from 'react'
import { photoUrl } from './lib/aftersales'
import type { HumanTicket } from './lib/humanCases'

export default function HumanPhotos({ ticket, token }: {ticket:HumanTicket;token?:string}) {
  const [images, setImages] = useState<{id:string;url:string}[]>([])
  const [error, setError] = useState('')
  useEffect(()=>{
    let active = true
    const owned: string[] = []
    setImages([]);setError('')
    void Promise.all(ticket.photos.map(async(photo)=>{
      const url = token === undefined ? photoUrl(ticket.case_id,photo.photo_id)
        : `/api/v1/mercury/operator/tickets/${encodeURIComponent(ticket.ticket_id)}/photos/${encodeURIComponent(photo.photo_id)}`
      const response = await fetch(url,{credentials:'include',headers:token===undefined?{}:{'X-Internal-Token':token}})
      if(!response.ok) throw new Error('照片读取失败，请刷新工单后重试')
      const local = URL.createObjectURL(await response.blob())
      if(!active) { URL.revokeObjectURL(local);return null }
      owned.push(local)
      return {id:photo.photo_id,url:local}
    })).then(result=>{if(active) setImages(result.filter((item):item is {id:string;url:string}=>item!==null))})
      .catch(error=>{if(active) setError(error instanceof Error?error.message:'照片读取失败')})
    return ()=>{active=false;owned.forEach(url=>URL.revokeObjectURL(url))}
  },[ticket.case_id,ticket.ticket_id,ticket.photos,token])
  return <div className="space-y-2">
    {error && <p role="alert" className="text-xs text-red-700">{error}</p>}
    {images.length>0 && <><p className="text-xs text-black/50">问题照片供人工核对。</p><div className="flex flex-wrap gap-2">{images.map(image=><a key={image.id} href={image.url} target="_blank" rel="noreferrer"><img className="h-24 w-24 rounded-xl object-cover" alt="待核对的问题照片" src={image.url} /></a>)}</div></>}
  </div>
}
