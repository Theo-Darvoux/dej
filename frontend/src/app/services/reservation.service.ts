import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ReservationService {
  private apiUrl = '/api/reservations';

  constructor(private http: HttpClient) {}

  createReservation(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/`, data, {
      withCredentials: true
    });
  }

  getReservations(): Observable<any> {
    return this.http.get(`${this.apiUrl}/my`, {
      withCredentials: true
    });
  }

  cancelReservation(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}`, {
      withCredentials: true
    });
  }
}
