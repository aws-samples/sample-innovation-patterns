import {
  useListProjectsQuery,
  useGetProjectQuery,
  useCreateProjectMutation,
  useDeleteProjectMutation,
} from '@/services/api'
import type { ProjectCreateRequest } from '@/services/api'

export function useProjectList() {
  const { data, error, isLoading, isFetching, refetch } = useListProjectsQuery()
  return {
    projects: data?.data || [],
    isLoading,
    isFetching,
    error,
    refetch,
  }
}

export function useProject(id: string | undefined) {
  const { data, error, isLoading } = useGetProjectQuery(id!, { skip: !id })
  return {
    project: data?.data || null,
    isLoading,
    error,
  }
}

export function useCreateProject() {
  const [create, { isLoading, error }] = useCreateProjectMutation()
  const createProject = async (data: ProjectCreateRequest) => {
    try {
      const result = await create(data).unwrap()
      return { success: true as const, data: result.data }
    } catch (err) {
      return { success: false as const, error: err }
    }
  }
  return { createProject, isLoading, error }
}

export function useDeleteProject() {
  const [remove, { isLoading }] = useDeleteProjectMutation()
  const deleteProject = async (id: string) => {
    try {
      await remove(id).unwrap()
      return { success: true as const }
    } catch (err) {
      return { success: false as const, error: err }
    }
  }
  return { deleteProject, isLoading }
}
