"use client";
import type { Report as ReportData } from "@/lib/api";
import { formatDate } from "@/lib/api";
export default function Report({ report }: { report: ReportData }) {
  const max = Math.max(...report.chart.map((row) => row.total), 1);
  return (
    <>
      <div className="report-grid">
        <section className="report-summary">
          <span className="stat-label">Your planned work, completed</span>
          <strong className="big-number">{report.percentage}%</strong>
          <div
            className="progress-track"
            role="progressbar"
            aria-label="Task completion"
            aria-valuenow={report.percentage}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <span style={{ width: `${report.percentage}%` }} />
          </div>
          <dl>
            <div>
              <dt>Completed</dt>
              <dd>{report.completed}</dd>
            </div>
            <div>
              <dt>Remaining</dt>
              <dd>{report.remaining}</dd>
            </div>
            <div>
              <dt>Planned tasks</dt>
              <dd>{report.total}</dd>
            </div>
            <div>
              <dt>Period</dt>
              <dd style={{ fontSize: 12 }}>
                {formatDate(report.start)} – {formatDate(report.last_day)}
              </dd>
            </div>
          </dl>
        </section>
        <section className="chart-panel">
          <header className="chart-header">
            <h3>
              {report.period === "year"
                ? "Your year, month by month"
                : "Small steps, day by day"}
            </h3>
            <div className="chart-legend">
              <span>
                <i />
                Completed
              </span>
              <span>
                <i />
                Remaining
              </span>
            </div>
          </header>
          <div
            className="chart-scroll"
            tabIndex={0}
            aria-label="Progress chart, scroll to see the full period"
          >
            <div className="chart">
              {report.chart.map((row) => (
                <div
                  key={row.label}
                  className="chart-column"
                  tabIndex={0}
                  aria-label={`${row.label}: ${row.completed} completed, ${row.remaining} remaining`}
                >
                  <div className="chart-stack" aria-hidden="true">
                    <div
                      className="chart-remaining"
                      style={{ height: (row.remaining / max) * 165 }}
                    />
                    <div
                      className="chart-done"
                      style={{ height: (row.completed / max) * 165 }}
                    />
                  </div>
                  <span>{row.label}</span>
                  <div className="chart-tip">
                    {row.completed} of {row.total} done
                  </div>
                </div>
              ))}
            </div>
          </div>
          <details className="chart-table">
            <summary>The numbers behind the picture</summary>
            <table>
              <caption className="sr-only">Completion by day or month</caption>
              <thead>
                <tr>
                  <th scope="col">Period</th>
                  <th scope="col">Done</th>
                  <th scope="col">Remaining</th>
                  <th scope="col">Total</th>
                </tr>
              </thead>
              <tbody>
                {report.chart.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    <td>{row.completed}</td>
                    <td>{row.remaining}</td>
                    <td>{row.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </section>
      </div>
      {!report.total && (
        <p className="banner" style={{ marginTop: 20 }}>
          No tasks planned in this period yet. Your progress will appear as you
          add them.
        </p>
      )}
      <p className="report-footnote">
        This reflects tasks scheduled in this calendar period, including future
        dates. Undated tasks use their creation date. Weeks start Sunday, in
        Riyadh time. It’s a little perspective—not a measure of your worth.
      </p>
    </>
  );
}
