// Adapted from shadcn's public Skeleton source, also listed on 21st.dev.
// MIT: see frontend/THIRD_PARTY_NOTICES.md.
import type { ComponentProps } from 'react'

export function Skeleton({ className = '', ...props }: ComponentProps<'div'>) {
  return <div {...props} className={'skeleton ' + className} aria-hidden="true" />
}

export function ResultSkeleton({ kind }: { kind: 'music' | 'books' | 'playlist' }) {
  return <div className={'result-skeletons ' + kind} aria-hidden="true">
    {[0, 1, 2].map(index => <div className="result-placeholder" key={index}>
      <Skeleton className="skeleton-art" />
      <div className="skeleton-copy"><Skeleton className="skeleton-title" /><Skeleton className="skeleton-author" /><Skeleton className="skeleton-detail" /></div>
    </div>)}
  </div>
}
