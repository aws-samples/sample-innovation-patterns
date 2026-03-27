import { baseApi } from './baseApi'

interface UploadResponse {
  message: string
}

export const uploadApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    uploadDocuments: builder.mutation<UploadResponse, FormData>({
      query: (formData) => ({
        url: '/api/v1/documents',
        method: 'POST',
        body: formData,
      }),
      invalidatesTags: ['passengers'],
    }),
  }),
})

export const { useUploadDocumentsMutation } = uploadApi
