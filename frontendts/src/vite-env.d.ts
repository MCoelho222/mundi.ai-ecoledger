/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_WEBSITE_DOMAIN: string;
  readonly VITE_EMAIL_VERIFICATION: string;
  readonly VITE_AUTH_MODE: string;
  readonly VITE_POSTHOG_API_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
