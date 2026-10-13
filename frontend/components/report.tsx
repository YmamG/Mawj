"use client";
import { useLanguage } from "@/components/language";
import type { Report as ReportData } from "@/lib/api";
import { formatDate as formatDateBase } from "@/lib/api";
export default function Report({ report }: { report: ReportData }) {
  const { t: translate, language } = useLanguage();
  const formatDate = (
    value: string | null,
    options?: Intl.DateTimeFormatOptions,
  ) => formatDateBase(value, options, language);

  const max = Math.max(...report.chart.map((row) => row.total), 1);
  return (
    <>
      <div className="report-grid">
        <section className="report-summary">
          <span className="stat-label">
            {translate("Your planned work, completed")}
          </span>
          <strong className="big-number">{report.percentage}%</strong>
          <div
            className="progress-track"
            role="progressbar"
            aria-label={translate("Task completion")}
            aria-valuenow={report.percentage}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <span style={{ width: `${report.percentage}%` }} />
          </div>
          <dl>
            <div>
              <dt>{translate("Completed")}</dt>
              <dd>{report.completed}</dd>
            </div>
            <div>
              <dt>{translate("Remaining")}</dt>
              <dd>{report.remaining}</dd>
            </div>
            <div>
              <dt>{translate("Planned tasks")}</dt>
              <dd>{report.total}</dd>
            </div>
            <div>
              <dt>{translate("Period")}</dt>
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
                ? translate("Your year, month by month")
                : translate("Small steps, day by day")}
            </h3>
            <div className="chart-legend">
              <span>
                <i /> {translate("Completed")}{" "}
              </span>
              <span>
                <i /> {translate("Remaining")}{" "}
              </span>
            </div>
          </header>
          <div
            className="chart-scroll"
            tabIndex={0}
            aria-label={translate(
              "Progress chart, scroll to see the full period",
            )}
          >
            <div className="chart">
              {report.chart.map((row) => (
                <div
                  key={translate(row.label)}
                  className="chart-column"
                  tabIndex={0}
                  aria-label={`${translate(row.label)}: ${row.completed} completed, ${row.remaining} remaining`}
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
                  <span>{translate(row.label)}</span>
                  <div className="chart-tip">
                    {row.completed} {translate("of")} {row.total}{" "}
                    {translate("done")}{" "}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <details className="chart-table">
            <summary>{translate("The numbers behind the picture")}</summary>
            <table>
              <caption className="sr-only">
                {translate("Completion by day or month")}
              </caption>
              <thead>
                <tr>
                  <th scope="col">{translate("Period")}</th>
                  <th scope="col">{translate("Done")}</th>
                  <th scope="col">{translate("Remaining")}</th>
                  <th scope="col">{translate("Total")}</th>
                </tr>
              </thead>
              <tbody>
                {report.chart.map((row) => (
                  <tr key={translate(row.label)}>
                    <th scope="row">{translate(row.label)}</th>
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
          {" "}
          {translate(
            "No tasks planned in this period yet. Your progress will appear as you add them.",
          )}{" "}
        </p>
      )}
      <p className="report-footnote">
        {" "}
        {translate(
          "This reflects tasks scheduled in this calendar period, including future dates. Undated tasks use their creation date. Weeks start Sunday, in Riyadh time. It’s a little perspective—not a measure of your worth.",
        )}{" "}
      </p>
    </>
  );
}
