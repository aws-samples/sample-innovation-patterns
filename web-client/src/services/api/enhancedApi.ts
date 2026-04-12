// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
// Endpoint overrides for generated API endpoints.
//
// Use appApi.injectEndpoints({ overrideExisting: true }) here to fix codegen
// issues without editing generated.ts. Example: if a backend route does NOT
// use a path converter like {param:path}, you may need to encodeURIComponent
// path parameters that contain special characters:
//
//   import { appApi } from './generated'
//
//   appApi.injectEndpoints({
//     overrideExisting: true,
//     endpoints: (build) => ({
//       getItemById: build.query({
//         query: (arg: { id: string }) => ({
//           url: `/api/v1/items/${encodeURIComponent(arg.id)}`,
//         }),
//         providesTags: ['items'],
//       }),
//     }),
//   })
//
// For the passenger endpoints, the backend uses {ticket:path} in FastAPI
// so encoding is not needed here — the server matches across slashes natively.
