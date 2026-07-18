import { Component } from "react";
import { I18nContext } from "./i18n";

export default class ErrorBoundary extends Component {
  static contextType = I18nContext;

  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      const { t } = this.context;
      return (
        <div className="errorBoundary">
          <h1>{t("error_boundary.title")}</h1>
          <pre>{this.state.error.message}</pre>
          <button onClick={() => window.location.reload()}>{t("error_boundary.reload")}</button>
        </div>
      );
    }
    return this.props.children;
  }
}