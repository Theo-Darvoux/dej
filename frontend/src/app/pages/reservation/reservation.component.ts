import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ReservationService } from '../../services/reservation.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-reservation',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reservation.component.html',
  styleUrls: ['./reservation.component.scss']
})
export class ReservationComponent implements OnInit {
  form = {
    date_reservation: '',
    heure_reservation: '',
    habite_residence: false,
    numero_chambre: '',
    numero_immeuble: '',
    adresse: ''
  };

  loading: boolean = false;
  error: string = '';
  success: boolean = false;
  minDate: string = '';

  constructor(
    private reservationService: ReservationService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
    }
    this.setMinDate();
  }

  setMinDate(): void {
    const today = new Date();
    today.setDate(today.getDate() + 1);
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    this.minDate = `${year}-${month}-${day}`;
  }

  onSubmit(): void {
    if (!this.form.date_reservation || !this.form.heure_reservation) {
      this.error = 'Veuillez remplir tous les champs obligatoires';
      return;
    }

    if (!this.form.habite_residence && !this.form.adresse) {
      this.error = 'Veuillez entrer une adresse';
      return;
    }

    this.loading = true;
    this.error = '';

    this.reservationService.createReservation(this.form).subscribe({
      next: (response) => {
        this.success = true;
        this.loading = false;
        setTimeout(() => {
          this.router.navigate(['/dashboard']);
        }, 2000);
      },
      error: (error) => {
        this.loading = false;
        this.error = error.error?.detail || 'Erreur lors de la réservation';
      }
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
