interface SjclStatic {
  encrypt(password: string, data: string): string;
  decrypt(password: string, cyphertext: string): string;
}

declare var sjcl: SjclStatic;
