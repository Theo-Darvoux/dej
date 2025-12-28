import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-verify',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './verify.component.html',
  styleUrls: ['./verify.component.scss']
})
export class VerifyComponent implements OnInit {
  code: string = '';
  email: string = '';
  loading: boolean = false;
  error: string = '';
  success: boolean = false;
  codeInputs: string[] = ['', '', '', '']; // For 4-digit code

  constructor(
    public router: Router,
    private authService: AuthService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.email = this.route.snapshot.queryParams['email'] || '';
    if (!this.email) {
      this.router.navigate(['/login']);
    }
  }

  onCodeInputChange(index: number, event: any): void {
    const input = event.target as HTMLInputElement;
    const value = input.value.replace(/[^0-9]/g, '');
    
    this.codeInputs[index] = value.charAt(0) || '';
    this.code = this.codeInputs.join('');
  }

  onKeyDown(index: number, event: KeyboardEvent): void {
    // Rien de spécial
  }

  onSubmit(): void {
    if (this.code.length !== 4) {
      this.error = 'Veuillez entrer tous les chiffres';
      return;
    }

    this.loading = true;
    this.error = '';

    this.authService.verifyCode(this.email, this.code).subscribe({
      next: (response) => {
        this.success = true;
        this.loading = false;
        setTimeout(() => {
          if (response.is_cotisant) {
            this.router.navigate(['/reservation']);
          } else {
            this.router.navigate(['/dashboard']);
          }
        }, 1500);
      },
      error: (error) => {
        this.loading = false;
        this.error = error.error?.detail || 'Code invalide ou expiré';
        this.codeInputs = ['', '', '', ''];
        this.code = '';
      }
    });
  }

  resendCode(): void {
    this.authService.requestCode(this.email).subscribe({
      next: () => {
        this.error = '';
        this.success = true;
        setTimeout(() => {
          this.success = false;
        }, 3000);
      },
      error: (error) => {
        this.error = error.error?.detail || 'Erreur lors de l\'envoi du code';
      }
    });
  }
}
