import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = '/api/auth';
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  constructor(private http: HttpClient) {
    this.checkAuthStatus();
  }

  requestCode(email: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/request-code`, { email });
  }

  verifyCode(email: string, code: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/verify`, { email, code }, {
      withCredentials: true
    }).pipe(
      tap((response: any) => {
        // Marquer comme authentifié dès que la vérification réussit
        localStorage.setItem('user_email', email);
        localStorage.setItem('is_verified', 'true');
        this.isAuthenticatedSubject.next(true);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('user_email');
    localStorage.removeItem('is_verified');
    this.isAuthenticatedSubject.next(false);
  }

  private hasToken(): boolean {
    return localStorage.getItem('is_verified') === 'true';
  }

  private checkAuthStatus(): void {
    this.isAuthenticatedSubject.next(this.hasToken());
  }

  getToken(): string | null {
    return localStorage.getItem('is_verified');
  }

  isAuthenticated(): boolean {
    return this.hasToken();
  }
}
