import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  email: string = '';
  loading: boolean = false;
  error: string = '';
  success: boolean = false;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/dashboard']);
    }
  }

  onSubmit(): void {
    if (!this.email) {
      this.error = 'Veuillez entrer votre email';
      return;
    }

    this.loading = true;
    this.error = '';

    this.authService.requestCode(this.email).subscribe({
      next: (response) => {
        this.success = true;
        this.loading = false;
        setTimeout(() => {
          this.router.navigate(['/verify'], { 
            queryParams: { email: this.email } 
          });
        }, 1500);
      },
      error: (error) => {
        this.loading = false;
        this.error = error.error?.detail || 'Erreur lors de l\'envoi du code';
      }
    });
  }
}
