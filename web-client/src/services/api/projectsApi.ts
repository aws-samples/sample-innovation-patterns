import { baseApi } from './baseApi'

export interface ProjectResponse {
  id: string
  name: string
  description: string | null
  created_at: string | null
}

export interface ProjectCreateRequest {
  name: string
  description?: string | null
}

interface ApiResponse<T> {
  data: T
}

export const projectsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listProjects: builder.query<ApiResponse<ProjectResponse[]>, void>({
      query: () => '/api/v1/projects',
      providesTags: ['projects'],
    }),
    getProject: builder.query<ApiResponse<ProjectResponse>, string>({
      query: (id) => `/api/v1/projects/${id}`,
      providesTags: (_r, _e, id) => [{ type: 'projects' as const, id }],
    }),
    createProject: builder.mutation<ApiResponse<ProjectResponse>, ProjectCreateRequest>({
      query: (data) => ({
        url: '/api/v1/projects',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['projects'],
    }),
    updateProject: builder.mutation<
      ApiResponse<ProjectResponse>,
      { id: string; data: Partial<ProjectCreateRequest> }
    >({
      query: ({ id, data }) => ({
        url: `/api/v1/projects/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (_r, _e, { id }) => ['projects', { type: 'projects' as const, id }],
    }),
    deleteProject: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/v1/projects/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['projects'],
    }),
  }),
})

export const {
  useListProjectsQuery,
  useGetProjectQuery,
  useCreateProjectMutation,
  useUpdateProjectMutation,
  useDeleteProjectMutation,
} = projectsApi
