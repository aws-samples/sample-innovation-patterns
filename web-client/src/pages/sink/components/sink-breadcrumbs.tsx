import { Link, useParams } from 'react-router'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'

function getComponentName(name: string) {
  return name.replace(/-/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

export function SinkBreadcrumbs() {
  const { name } = useParams<{ name: string }>()

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          {name ? (
            <BreadcrumbLink asChild>
              <Link to="/sink">Kitchen Sink</Link>
            </BreadcrumbLink>
          ) : (
            <BreadcrumbPage>Kitchen Sink</BreadcrumbPage>
          )}
        </BreadcrumbItem>
        {name && (
          <>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{getComponentName(name)}</BreadcrumbPage>
            </BreadcrumbItem>
          </>
        )}
      </BreadcrumbList>
    </Breadcrumb>
  )
}
