"use client";
import { useLanguage } from "@/components/language";
import Link from "next/link";
import {
  ArrowUpRight,
  ArrowRight,
  Check,
  CheckCircle,
  ListChecks,
  Notebook,
  ChartBar,
  Sparkle,
  ArrowDown,
  CalendarBlank,
  Plant,
  CaretRight,
} from "@phosphor-icons/react";
import { Brand, Wave } from "@/components/brand";
import { ThemePicker } from "@/components/theme";
function DayPreview() {
  const { t: translate, language } = useLanguage();

  return (
    <div
      className="day-preview"
      aria-label={translate("Illustrative example of Mawj, not account data")}
    >
      <div className="preview-top">
        <Brand href="/signup" />
        <span className="tiny">{translate("A glimpse of your day")}</span>
      </div>
      <div className="preview-greeting">
        <span className="eyebrow">{translate("YOUR SPACE, YOUR PACE")}</span>
        <h3>
          {" "}
          {translate("A little progress")} <br />{" "}
          {translate("goes a long way.")}{" "}
        </h3>
        <span className="preview-date">
          <CalendarBlank size={14} />{" "}
          {translate("Monday · an example day")}{" "}
        </span>
      </div>
      <div className="preview-task">
        <span className="check checked">
          <Check size={13} />
        </span>
        <span className="done">{translate("Read a chapter")}</span>
        <span className="mini-tag">{translate("Study")}</span>
      </div>
      <div className="preview-task">
        <span className="check" />
        <span>{translate("A walk, just for me")}</span>
        <span className="mini-tag">{translate("Personal")}</span>
      </div>
      <div className="preview-task">
        <span className="check" />
        <span>{translate("Put my thoughts on paper")}</span>
        <Notebook size={16} />
      </div>
      <div className="preview-bottom">
        <div>
          <span className="tiny">{translate("Small steps add up")}</span>
          <div className="preview-bars">
            {[22, 38, 28, 58, 44, 70, 54].map((height, i) => (
              <span key={i} style={{ height }} />
            ))}
          </div>
        </div>
        <div className="progress-ring">
          <Plant size={26} />
        </div>
      </div>
      <span className="example-label">{translate("Illustrative example")}</span>
    </div>
  );
}
export default function Home() {
  const { t: translate, language } = useLanguage();

  return (
    <>
      <header className="landing-header container">
        <Brand />
        <nav aria-label={translate("Main navigation")}>
          <a href="#how-it-works">{translate("How it works")}</a>
          <a href="#your-space">{translate("Your space")}</a>
        </nav>
        <div className="header-actions">
          <ThemePicker />
          <Link className="login-link" href="/login">
            {" "}
            {translate("Log in")}{" "}
          </Link>
          <Link className="button small" href="/signup">
            {" "}
            {translate("Find your flow")} <ArrowUpRight size={16} />
          </Link>
        </div>
      </header>
      <main id="main">
        <section className="hero container">
          <div className="hero-copy">
            <p className="eyebrow">
              <span className="status-dot" />{" "}
              {translate("A calmer way to get things done")}{" "}
            </p>
            <h1>
              {language === "ar" ? (
                <>مساحة لأفكارك.<br />وبال <em>أهدأ.</em></>
              ) : (
                <>A little space.<br />A <em>clearer</em> mind.</>
              )}
            </h1>
            <p className="hero-description">
              {" "}
              {translate("Some days, everything feels like a lot.")} <br />{" "}
              {translate(
                "Mawj gives your thoughts a home—and helps you turn the things that matter into small, doable steps.",
              )}{" "}
            </p>
            <div className="hero-actions">
              <Link href="/signup" className="button">
                {" "}
                {translate("Make room for your day")} <ArrowUpRight size={19} />
              </Link>
              <a href="#how-it-works" className="text-link">
                {" "}
                {translate("Take a look around")} <ArrowDown size={16} />
              </a>
            </div>
            <p className="hero-footnote">
              <CheckCircle size={16} />{" "}
              {translate("No crowded planners. No perfect-day pressure.")}{" "}
            </p>
          </div>
          <div className="hero-art">
            <div className="art-orbit orbit-one" />
            <div className="art-orbit orbit-two" />
            <div className="floating-note">
              <span className="note-pin" />
              <Notebook size={20} />
              <p>
                {" "}
                {translate("Less in your head.")} <br />
                <em>{translate("More room to breathe.")}</em>
              </p>
            </div>
            <DayPreview />
            <div className="floating-caption">
              <span className="small-wave">
                <Wave />
              </span>
              <span>
                {" "}
                {translate("A thought. A step.")} <br />
                <strong>{translate("A little more clarity.")}</strong>
              </span>
            </div>
          </div>
        </section>
        <div className="quiet-strip container">
          <span>{translate("Built for real days.")}</span>
          <span>
            <Notebook size={18} /> {translate("A place to reflect")}{" "}
          </span>
          <span>
            <ListChecks size={18} />{" "}
            {translate("A plan that feels doable")}{" "}
          </span>
          <span>
            <ChartBar size={18} /> {translate("Progress you can see")}{" "}
          </span>
        </div>
        <section id="how-it-works" className="story-section container">
          <div className="section-intro">
            <p className="eyebrow">
              {translate("From a busy mind to a gentler day")}
            </p>
            <h2>
              {" "}
              {translate("You don’t need another list.")} <br />{" "}
              {translate("You need a little")} <em>{translate("flow.")}</em>
            </h2>
            <p>
              {" "}
              {translate(
                "Start with what’s on your mind. We’ll help you find what comes next.",
              )}{" "}
            </p>
          </div>
          <div className="journey">
            <article>
              <span className="step-number">01</span>
              <Notebook size={29} />
              <h3>{translate("Let it out.")}</h3>
              <p>
                {" "}
                {translate(
                  "A thought, a feeling, a messy paragraph. Your journal doesn’t need to be perfect to be useful.",
                )}{" "}
              </p>
            </article>
            <span className="journey-arrow">
              <ArrowRight />
            </span>
            <article>
              <span className="step-number">02</span>
              <ListChecks size={29} />
              <h3>{translate("Find your next step.")}</h3>
              <p>
                {" "}
                {translate(
                  "Review task suggestions from your notes. Keep what’s useful, leave the rest. You always decide.",
                )}{" "}
              </p>
            </article>
            <span className="journey-arrow">
              <ArrowRight />
            </span>
            <article>
              <span className="step-number">03</span>
              <ChartBar size={29} />
              <h3>{translate("Notice the progress.")}</h3>
              <p>
                {" "}
                {translate(
                  "See what you’ve done this week, month, or year. Small wins deserve a little space, too.",
                )}{" "}
              </p>
            </article>
          </div>
        </section>
        <section id="your-space" className="space-section container">
          <div className="space-visual">
            <div className="journal-example">
              <div className="journal-label">
                <Notebook size={18} /> {translate("A page just for you")}{" "}
                <span>{translate("EXAMPLE")}</span>
              </div>
              <p className="handwritten">
                {" "}
                {translate("Today felt a little scattered.")} <br />
                {translate("I want to make time to study,")} <br />{" "}
                {translate("and remember to slow down.")}{" "}
              </p>
              <div className="suggested-note">
                <Sparkle size={18} />
                <span>{translate("One possible next step")}</span>
                <div>
                  <span className="check" />{" "}
                  {translate("Review my study notes")}{" "}
                  <ArrowUpRight size={16} />
                </div>
              </div>
            </div>
            <span className="visual-caption">
              {" "}
              {translate("Your thoughts don’t have to stay tangled.")}{" "}
            </span>
          </div>
          <div className="space-copy">
            <p className="eyebrow">
              {translate("More personal. Less complicated.")}
            </p>
            <h2>
              {" "}
              {translate("A space that")} <br /> {translate("feels like")}{" "}
              <em>{translate("you.")}</em>
            </h2>
            <p>
              {" "}
              {translate(
                "Your journal, your tasks, your rhythm. Bring them together in one quiet place, with just enough structure to help.",
              )}{" "}
            </p>
            <ul>
              <li>
                <CheckCircle /> {translate("Keep the details optional")}{" "}
              </li>
              <li>
                <CheckCircle />{" "}
                {translate("Build a routine with repeating tasks")}{" "}
              </li>
              <li>
                <CheckCircle />{" "}
                {translate("Choose a palette that fits your mood")}{" "}
              </li>
              <li>
                <CheckCircle />{" "}
                {translate("Keep your notes private to your account")}{" "}
              </li>
            </ul>
            <div className="palette-showcase">
              <ThemePicker />
              <span>
                {" "}
                {translate("Five moods. One familiar space.")} <br />
                <small>
                  {translate("Try the colors—this page changes with you.")}
                </small>
              </span>
            </div>
          </div>
        </section>
        <section className="closing-section container">
          <div className="closing-decoration">
            <Wave />
          </div>
          <p className="eyebrow">
            {translate("One small step is a good start")}
          </p>
          <h2>
            {" "}
            {translate("Let’s make a little")} <br /> {translate("room for")}{" "}
            <em>{translate("you.")}</em>
          </h2>
          <p>
            {" "}
            {translate(
              "You don’t have to have it all figured out.",
            )} <br /> {translate("Just start with what’s on your mind.")}{" "}
          </p>
          <Link href="/signup" className="button">
            {" "}
            {translate("Start your first page")} <ArrowUpRight size={19} />
          </Link>
        </section>
      </main>
      <footer className="landing-footer container">
        <Brand />
        <span>{translate("Thoughts into plans. Plans into progress.")}</span>
        <div>
          <Link href="/privacy">{translate("Privacy")}</Link>
          <Link href="/about">{translate("About Mawj")}</Link>
          <span>
            {" "}
            {translate("Made by")}{" "}
            <a
              href="https://github.com/ymamggg-jpg"
              target="_blank"
              rel="noopener noreferrer"
            >
              {" "}
              {translate("Ymam")}{" "}
            </a>
          </span>
        </div>
      </footer>
    </>
  );
}
