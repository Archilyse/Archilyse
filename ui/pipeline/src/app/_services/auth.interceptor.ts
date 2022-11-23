import { tap } from 'rxjs/operators';
import { Injectable } from '@angular/core';
import cookie from 'js-cookie';
import jwt_decode from 'jwt-decode';
import { HttpHandler, HttpRequest, HttpInterceptor, HttpErrorResponse } from '@angular/common/http';
import { LocalStorage } from '../_shared-libraries/LocalStorage';
import { Router } from '@angular/router';

const AUTH_ERRORS = [401, 403, 422];
const AUTH_TOKEN = 'access_token';
const ROLES = 'roles';
const EXPIRATION_DAYS = 7;

interface IdentityType {
  id: number;
  client_id: number;
  group_id: number;
  name: string;
}

export function authenticate({ access_token, roles }) {
  cookie.set(AUTH_TOKEN, access_token, { expires: EXPIRATION_DAYS });
  cookie.set(ROLES, roles, { expires: EXPIRATION_DAYS });

  // Old, probably deprecated way of authenticating, keeping it here just in case
  LocalStorage.storeApiToken(access_token);
  LocalStorage.storeApiRoles(roles);
}
export function getUserInfo(): IdentityType {
  const accessToken = cookie.get(AUTH_TOKEN);
  const decodedToken: any = jwt_decode(accessToken);
  return decodedToken && decodedToken.sub;
}

export function getAuthToken() {
  const cookieToken = cookie.get(AUTH_TOKEN);
  return cookieToken ? cookieToken : LocalStorage.getApiToken();
}

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private router: Router) {}
  intercept(req: HttpRequest<any>, next: HttpHandler) {
    const clonedRequest = req.clone({ setHeaders: { Authorization: `Bearer ${getAuthToken()}` } });
    return next.handle(clonedRequest).pipe(
      tap(
        () => {},
        (error: any) => {
          if (error instanceof HttpErrorResponse) {
            if (AUTH_ERRORS.includes(error.status)) {
              location.replace(`/login?previousUrl=${encodeURI(this.router.url)}`);
            }
          }
        }
      )
    );
  }
}
