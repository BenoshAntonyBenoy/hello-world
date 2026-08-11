import { Link } from 'react-router-dom'
import { Page } from '@/components/ui'

export default function NotFound() {
  return (
    <Page className="max-w-xl">
      <div className="py-16 text-center">
        <p className="font-mono text-sm text-brand">404</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
          There is nothing at this address
        </h1>
        <p className="mt-2 text-sm text-muted">
          The page may have moved, or the link may be wrong.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <Link to="/" className="btn-primary">
            Go home
          </Link>
          <Link to="/search" className="btn-secondary">
            Browse roles
          </Link>
        </div>
      </div>
    </Page>
  )
}
