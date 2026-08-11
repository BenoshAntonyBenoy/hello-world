/** Shared by the live and static clients, so neither has to import the other. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/** Thrown by features that genuinely cannot work without the Python backend. */
export class UnsupportedInStaticBuild extends ApiError {
  constructor(feature: string) {
    super(
      `${feature} needs the Python extraction service, which cannot run on ` +
        `static hosting. Run the project locally to use it.`,
      501,
    )
    this.name = 'UnsupportedInStaticBuild'
  }
}
