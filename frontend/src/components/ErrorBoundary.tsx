import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Page } from './ui'

interface Props {
  children: ReactNode
  /** Changes to this reset the boundary — pass the pathname so navigating
   *  away from a broken route recovers instead of staying blank. */
  resetKey?: string
}

interface State {
  error: Error | null
}

/**
 * Catches render-time errors so one bad component does not blank the site.
 *
 * `useAsync` already handles failed requests; this is for the other kind — a
 * malformed payload reaching a component that assumed a field was present,
 * which without a boundary unmounts the whole tree and leaves a white page
 * with no way back.
 *
 * Must be a class: there is no hook equivalent of componentDidCatch.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled render error', error, info.componentStack)
  }

  componentDidUpdate(previous: Props) {
    if (this.state.error && previous.resetKey !== this.props.resetKey) {
      this.setState({ error: null })
    }
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <Page className="max-w-xl">
        <div className="card p-8 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-high/10 text-high">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
              <path
                d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <p className="text-sm font-medium">This page failed to render</p>
          <p className="mx-auto mt-1 max-w-md text-sm text-muted">
            Something in the data reached a part of the page that could not handle it. Nothing you
            did caused this, and nothing you saved has been lost.
          </p>
          <p className="mx-auto mt-3 max-w-md break-words font-mono text-xs text-faint">
            {this.state.error.message}
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-2">
            <button
              type="button"
              onClick={() => this.setState({ error: null })}
              className="btn-primary"
            >
              Try again
            </button>
            <a href="./" className="btn-secondary">
              Go home
            </a>
          </div>
        </div>
      </Page>
    )
  }
}
