import request from '../utils/request'

export function loginApi(data) {
  return request.post('/login', data)
}

export function getUserInfoApi() {
  return request.get('/userinfo')
}

export function registerApi(data) {
  return request.post('/register', data)
}

export function sendCodeApi(email) {
  return request.post('/sendcode', {email})
}

export function updateUserInfoApi(data) {
  return request.post('/updateUserInfo', data)
}

export function emailIfexist(email) {
  return request.post('/checkemail', {email})
}

export function uploadApi(data) {
  return request.post('/upload', data)
}

export function importApi(data) {
  return request.post('/import', data)
}

export function cancelImportApi(data) {
  return request.post('/cancel', data)
}

export function getfileInfo(params) {
  return request.get('/getfileinfo', {params})
}

// export function downloadFile(fileid, data) {
//   return request.get(`/download/${fileid}`, data)
// }

// export function downloadBatchFiles(ids, format) {
//   return request.post(
//     '/download/batch',
//     { ids: ids,
//       format: format
//     },
//     { responseType: 'blob' }
//   )
// }

export function fetchAttrSuggestions(fieldNames) {
  return request.post('/attrmatch', {fieldNames})
}

export function checkEngnameExist(engName) {
  return request.post('/checkEngnameExist', {engName})
}

export function checkfilename(filename) {
  return request.post('/checkfilename', {filename})
}

export function querydata(data) {
  return request.post('/querydata', data)
}

export function deletefile(fileid) {
  return request.post('/deletefile', {fileid})
}