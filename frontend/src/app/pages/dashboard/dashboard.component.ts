import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ReservationService } from '../../services/reservation.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  reservations: any[] = [];
  loading: boolean = true;
  error: string = '';

  constructor(
    private reservationService: ReservationService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return;
    }
    this.loadReservations();
  }

  loadReservations(): void {
    this.reservationService.getReservations().subscribe({
      next: (response) => {
        this.reservations = response.reservations || [];
        this.loading = false;
      },
      error: (error) => {
        this.loading = false;
        this.error = error.error?.detail || 'Erreur lors du chargement';
      }
    });
  }

  cancelReservation(id: string): void {
    if (confirm('Êtes-vous sûr de vouloir annuler cette réservation ?')) {
      this.reservationService.cancelReservation(id).subscribe({
        next: () => {
          this.loadReservations();
        },
        error: (error) => {
          this.error = error.error?.detail || 'Erreur lors de l\'annulation';
        }
      });
    }
  }

  newReservation(): void {
    this.router.navigate(['/reservation']);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
