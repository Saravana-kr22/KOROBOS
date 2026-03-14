/*
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
*/
import Image from "next/image";

import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.panel}>
        <div className={styles.brand}>
          <Image
            src="/KOROBOS-logo.svg"
            alt="KOROBOS logo"
            className={styles.logo}
            width={220}
            height={220}
            priority
          />
          <div className={styles.brandText}>
            <span className={styles.eyebrow}>KOROBOS Frontend</span>
            <h1 className={styles.heading}>Frontend runtime is live.</h1>
          </div>
        </div>

        <p className={styles.description}>
          The Docker stack is serving the Next.js app, the API gateway, and the
          Kafka-backed backend services together. This page was switched to
          plain CSS so the frontend no longer depends on a missing Tailwind
          PostCSS adapter at runtime.
        </p>

        <div className={styles.actions}>
          <a className={styles.primaryAction} href="http://localhost:8080/docs">
            Open API Gateway Docs
          </a>
          <a
            className={styles.secondaryAction}
            href="http://localhost:8080/health"
            target="_blank"
            rel="noopener noreferrer"
          >
            Check Gateway Health
          </a>
        </div>

        <div className={styles.meta}>
          <div className={styles.metaCard}>
            <span className={styles.metaLabel}>Frontend</span>
            <p className={styles.metaValue}>Next.js dev server on port 3000</p>
          </div>
          <div className={styles.metaCard}>
            <span className={styles.metaLabel}>Gateway</span>
            <p className={styles.metaValue}>
              FastAPI + Redis-backed rate limiting
            </p>
          </div>
          <div className={styles.metaCard}>
            <span className={styles.metaLabel}>Event Backbone</span>
            <p className={styles.metaValue}>
              Kafka TLS/SASL broker, exporter, and topic init
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
