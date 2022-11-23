import { auth } from 'archilyse-ui-components';

export default (role = 'ADMIN') => {
  const mockToken =
    'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY1NDg1MDg3OSwianRpIjoiYTFiZDczYTUtZjk1MS00YWUyLTk4ZGMtZGQ2ZmMwYzhmNmI1IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiZ3JvdXBfaWQiOjEsImNsaWVudF9pZCI6bnVsbH0sIm5iZiI6MTY1NDg1MDg3OSwiY3NyZiI6ImU0ZTYzYTZjLThmMTgtNGRmYy04YTExLTcwN2RjMDFjYTI0NyIsImV4cCI6MTY1NDg1MDkzOX0.JmxFa4hzOmyOZ1U9r1hIKoQHi7CZc1-prBLaaE4kodQ';
  const mockRoles = [role];
  auth.authenticate(mockToken, mockRoles);
};
