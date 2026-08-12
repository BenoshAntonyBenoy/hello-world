import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Layout } from '@/components/Layout'
import Landing from '@/pages/Landing'
import Search from '@/pages/Search'
import RoleDashboard from '@/pages/RoleDashboard'
import RoleSkills from '@/pages/RoleSkills'
import RoleRoadmap from '@/pages/RoleRoadmap'
import RoleJobs from '@/pages/RoleJobs'
import Trends from '@/pages/Trends'
import Profile from '@/pages/Profile'
import SkillGap from '@/pages/SkillGap'
import Analyze from '@/pages/Analyze'
import About from '@/pages/About'
import NotFound from '@/pages/NotFound'

/** Reset scroll on navigation — without this, moving between role tabs lands
 *  the reader halfway down the next page. */
function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior })
  }, [pathname])
  return null
}

export default function App() {
  const { pathname } = useLocation()

  return (
    <Layout>
      <ScrollToTop />
      {/* Keyed on the path so navigating away from a route that threw clears
          the error, rather than trapping the user on the fallback. */}
      <ErrorBoundary resetKey={pathname}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/search" element={<Search />} />
          <Route path="/jobs/:role" element={<RoleDashboard />} />
          <Route path="/jobs/:role/skills" element={<RoleSkills />} />
          <Route path="/jobs/:role/roadmap" element={<RoleRoadmap />} />
          <Route path="/jobs/:role/listings" element={<RoleJobs />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/skill-gap" element={<SkillGap />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </ErrorBoundary>
    </Layout>
  )
}
