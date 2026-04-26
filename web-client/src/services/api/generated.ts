// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { baseApi as api } from "./baseApi";
export const addTagTypes = ["passengers", "sse", "jobs"] as const;
const injectedRtkApi = api
    .enhanceEndpoints({
        addTagTypes,
    })
    .injectEndpoints({
        endpoints: (build) => ({
            listPassengersApiV1PassengersGet: build.query<
                ListPassengersApiV1PassengersGetApiResponse,
                ListPassengersApiV1PassengersGetApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/passengers`,
                    params: {
                        limit: queryArg.limit,
                        pclass: queryArg.pclass,
                        survived: queryArg.survived,
                        sex: queryArg.sex,
                        embarked: queryArg.embarked,
                    },
                }),
                providesTags: ["passengers"],
            }),
            createPassengerApiV1PassengersPost: build.mutation<
                CreatePassengerApiV1PassengersPostApiResponse,
                CreatePassengerApiV1PassengersPostApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/passengers`,
                    method: "POST",
                    body: queryArg.titanicPassengerCreate,
                }),
                invalidatesTags: ["passengers"],
            }),
            getPassengerApiV1PassengersTicketGet: build.query<
                GetPassengerApiV1PassengersTicketGetApiResponse,
                GetPassengerApiV1PassengersTicketGetApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/passengers/${queryArg.ticket}`,
                }),
                providesTags: ["passengers"],
            }),
            updatePassengerApiV1PassengersTicketPut: build.mutation<
                UpdatePassengerApiV1PassengersTicketPutApiResponse,
                UpdatePassengerApiV1PassengersTicketPutApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/passengers/${queryArg.ticket}`,
                    method: "PUT",
                    body: queryArg.titanicPassengerCreate,
                }),
                invalidatesTags: ["passengers"],
            }),
            deletePassengerApiV1PassengersTicketDelete: build.mutation<
                DeletePassengerApiV1PassengersTicketDeleteApiResponse,
                DeletePassengerApiV1PassengersTicketDeleteApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/passengers/${queryArg.ticket}`,
                    method: "DELETE",
                }),
                invalidatesTags: ["passengers"],
            }),
            sseEchoApiV1SseEchoGet: build.query<
                SseEchoApiV1SseEchoGetApiResponse,
                SseEchoApiV1SseEchoGetApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/sse/echo`,
                    params: {
                        message: queryArg.message,
                    },
                }),
                providesTags: ["sse"],
            }),
            playgroundConverseStreamApiV1SsePlaygroundConversePost:
                build.mutation<
                    PlaygroundConverseStreamApiV1SsePlaygroundConversePostApiResponse,
                    PlaygroundConverseStreamApiV1SsePlaygroundConversePostApiArg
                >({
                    query: (queryArg) => ({
                        url: `/api/v1/sse/playground/converse`,
                        method: "POST",
                        body: queryArg.converseRequest,
                    }),
                    invalidatesTags: ["sse"],
                }),
            sseJobStatusApiV1SseJobsJobIdGet: build.query<
                SseJobStatusApiV1SseJobsJobIdGetApiResponse,
                SseJobStatusApiV1SseJobsJobIdGetApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/sse/jobs/${queryArg.jobId}`,
                }),
                providesTags: ["sse"],
            }),
            submitJobApiV1JobsPost: build.mutation<
                SubmitJobApiV1JobsPostApiResponse,
                SubmitJobApiV1JobsPostApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/jobs`,
                    method: "POST",
                    body: queryArg.jobCreate,
                }),
                invalidatesTags: ["jobs"],
            }),
            listJobsApiV1JobsGet: build.query<
                ListJobsApiV1JobsGetApiResponse,
                ListJobsApiV1JobsGetApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/jobs`,
                    params: {
                        limit: queryArg.limit,
                        status: queryArg.status,
                        job_type: queryArg.jobType,
                    },
                }),
                providesTags: ["jobs"],
            }),
            getJobApiV1JobsJobIdGet: build.query<
                GetJobApiV1JobsJobIdGetApiResponse,
                GetJobApiV1JobsJobIdGetApiArg
            >({
                query: (queryArg) => ({
                    url: `/api/v1/jobs/${queryArg.jobId}`,
                }),
                providesTags: ["jobs"],
            }),
            healthHealthGet: build.query<
                HealthHealthGetApiResponse,
                HealthHealthGetApiArg
            >({
                query: () => ({ url: `/health` }),
                providesTags: [],
            }),
            versionVersionGet: build.query<
                VersionVersionGetApiResponse,
                VersionVersionGetApiArg
            >({
                query: () => ({ url: `/version` }),
                providesTags: [],
            }),
        }),
        overrideExisting: false,
    });
export { injectedRtkApi as appApi };
export type ListPassengersApiV1PassengersGetApiResponse =
    /** status 200 Successful Response */ TitanicPassengerResponse[];
export type ListPassengersApiV1PassengersGetApiArg = {
    limit?: number;
    pclass?: number | null;
    survived?: number | null;
    sex?: string | null;
    embarked?: string | null;
};
export type CreatePassengerApiV1PassengersPostApiResponse =
    /** status 201 Successful Response */ TitanicPassengerResponse;
export type CreatePassengerApiV1PassengersPostApiArg = {
    titanicPassengerCreate: TitanicPassengerCreate;
};
export type GetPassengerApiV1PassengersTicketGetApiResponse =
    /** status 200 Successful Response */ TitanicPassengerResponse;
export type GetPassengerApiV1PassengersTicketGetApiArg = {
    ticket: string;
};
export type UpdatePassengerApiV1PassengersTicketPutApiResponse =
    /** status 200 Successful Response */ TitanicPassengerResponse;
export type UpdatePassengerApiV1PassengersTicketPutApiArg = {
    ticket: string;
    titanicPassengerCreate: TitanicPassengerCreate;
};
export type DeletePassengerApiV1PassengersTicketDeleteApiResponse =
    /** status 200 Successful Response */ any;
export type DeletePassengerApiV1PassengersTicketDeleteApiArg = {
    ticket: string;
};
export type SseEchoApiV1SseEchoGetApiResponse =
    /** status 200 Successful Response */ any;
export type SseEchoApiV1SseEchoGetApiArg = {
    message?: string;
};
export type PlaygroundConverseStreamApiV1SsePlaygroundConversePostApiResponse =
    /** status 200 Successful Response */ any;
export type PlaygroundConverseStreamApiV1SsePlaygroundConversePostApiArg = {
    converseRequest: ConverseRequest;
};
export type SseJobStatusApiV1SseJobsJobIdGetApiResponse =
    /** status 200 Successful Response */ any;
export type SseJobStatusApiV1SseJobsJobIdGetApiArg = {
    jobId: string;
};
export type SubmitJobApiV1JobsPostApiResponse =
    /** status 202 Successful Response */ JobResponse;
export type SubmitJobApiV1JobsPostApiArg = {
    jobCreate: JobCreate;
};
export type ListJobsApiV1JobsGetApiResponse =
    /** status 200 Successful Response */ JobResponse[];
export type ListJobsApiV1JobsGetApiArg = {
    limit?: number;
    status?: string | null;
    jobType?: string | null;
};
export type GetJobApiV1JobsJobIdGetApiResponse =
    /** status 200 Successful Response */ JobResponse;
export type GetJobApiV1JobsJobIdGetApiArg = {
    jobId: string;
};
export type HealthHealthGetApiResponse =
    /** status 200 Successful Response */ any;
export type HealthHealthGetApiArg = void;
export type VersionVersionGetApiResponse =
    /** status 200 Successful Response */ any;
export type VersionVersionGetApiArg = void;
export type TitanicPassengerResponse = {
    ticket: string;
    name: string;
    pclass: number;
    survived: number;
    sex: string;
    age?: number | null;
    sibsp: number;
    parch: number;
    fare?: number | null;
    cabin?: string | null;
    embarked?: string | null;
    boat?: string | null;
    body?: number | null;
    home_dest?: string | null;
    analysis?: {
        [key: string]: any;
    } | null;
};
export type ValidationError = {
    loc: (string | number)[];
    msg: string;
    type: string;
};
export type HttpValidationError = {
    detail?: ValidationError[];
};
export type TitanicPassengerCreate = {
    ticket: string;
    name: string;
    pclass: number;
    survived: number;
    sex: string;
    age?: number | null;
    sibsp?: number;
    parch?: number;
    fare?: number | null;
    cabin?: string | null;
    embarked?: string | null;
    boat?: string | null;
    body?: number | null;
    home_dest?: string | null;
    analysis?: string | null;
};
export type ConverseTurn = {
    role: string;
    text: string;
};
export type ConverseRequest = {
    model_id: string;
    messages: ConverseTurn[];
    system_prompt?: string;
    temperature?: number | null;
    max_tokens?: number;
    top_p?: number | null;
};
export type JobResponse = {
    job_id: string;
    status: string;
    job_type: string;
    input_data: {
        [key: string]: any;
    };
    metadata?: {
        [key: string]: any;
    } | null;
    error?: string | null;
    created_at: string;
    updated_at: string;
};
export type JobCreate = {
    job_type?: string;
    input_data: {
        [key: string]: any;
    };
};
export const {
    useListPassengersApiV1PassengersGetQuery,
    useCreatePassengerApiV1PassengersPostMutation,
    useGetPassengerApiV1PassengersTicketGetQuery,
    useUpdatePassengerApiV1PassengersTicketPutMutation,
    useDeletePassengerApiV1PassengersTicketDeleteMutation,
    useSseEchoApiV1SseEchoGetQuery,
    usePlaygroundConverseStreamApiV1SsePlaygroundConversePostMutation,
    useSseJobStatusApiV1SseJobsJobIdGetQuery,
    useSubmitJobApiV1JobsPostMutation,
    useListJobsApiV1JobsGetQuery,
    useGetJobApiV1JobsJobIdGetQuery,
    useHealthHealthGetQuery,
    useVersionVersionGetQuery,
} = injectedRtkApi;
