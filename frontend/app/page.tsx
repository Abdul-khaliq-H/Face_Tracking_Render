import Link from "next/link";

const features = [
  {
    title: "Built for creator footage",
    body: "Upload vertical videos, interviews, tutorials, or talking-head reels and keep the subject locked in frame.",
  },
  {
    title: "Fast job processing",
    body: "Queued workers let multiple customers upload at the same time without blocking the web app.",
  },
  {
    title: "Download-ready output",
    body: "Preview the processed file in the browser and download the final rendered video when it finishes.",
  },
];

const samples = [
  {
    title: "Podcast clips",
    body: "Turn long-form conversations into centered talking-head shorts for Instagram, TikTok, and YouTube Shorts.",
  },
  {
    title: "Solo creator tutorials",
    body: "Keep the face tracked while the creator moves naturally during explanations, demos, and product showcases.",
  },
];

export default function HomePage() {
  return (
    <main className="shell">
      <section className="hero">
        <div className="card hero-copy">
          <div className="eyebrow">Micro SaaS for social media creators</div>
          <h1>Automatic face tracking for creator videos.</h1>
          <p>
            CreatorTrack helps creators upload raw footage and get back a face-tracked video that is ready for editing,
            publishing, or repurposing into short-form content.
          </p>
          <div className="cta-row">
            <Link href="/try-now" className="primary-button">
              Try now
            </Link>
            <Link href="/sign-in" className="secondary-button">
              Sign in
            </Link>
          </div>
        </div>

        <div className="card hero-panel">
          <div className="preview-frame">
            <div className="preview-overlay">
              <strong>Sample workflow</strong>
              <p>
                Upload video -> face tracking runs in the worker -> preview the output -> download the processed file.
              </p>
            </div>
          </div>
          <div className="pill">Made for talking-head, tutorial, interview, and reaction videos</div>
        </div>
      </section>

      <section>
        <h2 className="section-title">Why creators use it</h2>
        <p className="section-copy">
          The product is designed to feel simple on the surface while using a backend job system that can serve many
          customers concurrently.
        </p>
        <div className="feature-grid">
          {features.map((feature) => (
            <article className="card feature-card" key={feature.title}>
              <strong>{feature.title}</strong>
              <p className="status-text">{feature.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2 className="section-title">Sample use cases</h2>
        <p className="section-copy">
          You can swap in your real model-backed Python pipeline while keeping this same customer experience.
        </p>
        <div className="sample-grid">
          {samples.map((sample) => (
            <article className="card sample-card" key={sample.title}>
              <div className="pill">Sample</div>
              <strong>{sample.title}</strong>
              <p className="status-text">{sample.body}</p>
              <Link href="/try-now" className="secondary-button">
                See the upload flow
              </Link>
            </article>
          ))}
        </div>
      </section>

      <p className="footer-note">Deploy this stack on Railway, Render, Fly.io, or a VPS using Docker.</p>
    </main>
  );
}

