// Every error response from the backend follows the same shape:
// { success: false, message: "...", errors: [...] }. Pulling this out
// into one function means every form in the app shows errors the same
// way, instead of each one guessing at error.response.data shape.
export function getErrorMessage(error) {
  const data = error?.response?.data
  if (data?.errors?.length) {
    return data.errors.join(' ')
  }
  if (data?.message) {
    return data.message
  }
  if (error?.message === 'Network Error') {
    return "Can't reach the server. Is the backend running?"
  }
  return 'Something went wrong. Please try again.'
}
