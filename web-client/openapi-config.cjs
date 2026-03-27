const config = {
  schemaFile: './openapi-schema.json',
  apiFile: './src/services/api/baseApi.ts',
  apiImport: 'baseApi',
  outputFile: './src/services/api/generated.ts',
  exportName: 'appApi',
  hooks: true,
  tag: true,
}

module.exports = config
