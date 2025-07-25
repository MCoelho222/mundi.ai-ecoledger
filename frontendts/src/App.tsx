// Copyright Bunting Labs, Inc. 2025

import { cogProtocol } from "@geomatico/maplibre-cog-protocol";
import maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";
import { useEffect } from "react";
import * as reactRouterDom from "react-router-dom";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import SuperTokens, { SuperTokensWrapper } from "supertokens-auth-react";
import EmailPassword from "supertokens-auth-react/recipe/emailpassword";
import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";
import EmailVerification from "supertokens-auth-react/recipe/emailverification";
import { EmailVerificationPreBuiltUI } from "supertokens-auth-react/recipe/emailverification/prebuiltui";
import Session, { SessionAuth } from "supertokens-auth-react/recipe/session";
import { getSuperTokensRoutesForReactRouterDom } from "supertokens-auth-react/ui";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Toaster } from "@/components/ui/sonner";

import MapsList from "./components/MapsList";
import ProjectView from "./components/ProjectView";
import PostGISDocumentation from "./pages/PostGISDocumentation";
import "./App.css";

const websiteDomain = import.meta.env.VITE_WEBSITE_DOMAIN;
if (!websiteDomain) {
  throw new Error(
    "VITE_WEBSITE_DOMAIN is not defined. Please set it in your .env file or build environment."
  );
}

const emailVerificationMode = import.meta.env.VITE_EMAIL_VERIFICATION;
if (
  emailVerificationMode !== "require" &&
  emailVerificationMode !== "disable"
) {
  throw new Error(
    "VITE_EMAIL_VERIFICATION must be either 'require' or 'disable'"
  );
}
const emailVerificationEnabled = emailVerificationMode === "require";

const authMode = import.meta.env.VITE_AUTH_MODE;
const authEnabled = authMode !== "disabled";

// Only initialize SuperTokens if auth is enabled
if (authEnabled) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recipeList: any[] = [EmailPassword.init(), Session.init()];
  if (emailVerificationEnabled) {
    recipeList.push(EmailVerification.init({ mode: "REQUIRED" }));
  }

  SuperTokens.init({
    appInfo: {
      appName: "Mundi",
      apiDomain: websiteDomain,
      websiteDomain: websiteDomain,
      apiBasePath: "/supertokens",
      websiteBasePath: "/auth",
    },
    recipeList,
    style: `
    [data-supertokens~="container"] {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }`,
  });
}

import { useState } from "react";
import { ProjectState } from "./lib/types";

function AppContent() {
  const [projectState, setProjectState] = useState<ProjectState>({
    type: "not_logged_in",
  });

  useEffect(() => {
    const protocol = new Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);
    maplibregl.addProtocol("cog", cogProtocol);
    return () => {
      maplibregl.removeProtocol("pmtiles");
      maplibregl.removeProtocol("cog");
    };
  }, []);

  // If auth is disabled, directly load projects without session check
  if (!authEnabled) {
    return (
      <AppContentWithoutAuth
        projectState={projectState}
        setProjectState={setProjectState}
      />
    );
  }

  // Auth is enabled, use the session context
  return (
    <SuperTokensWrapper>
      <AppContentWithAuth
        projectState={projectState}
        setProjectState={setProjectState}
      />
    </SuperTokensWrapper>
  );
}

function AppContentWithoutAuth({
  projectState,
  setProjectState,
}: {
  projectState: ProjectState;
  setProjectState: React.Dispatch<React.SetStateAction<ProjectState>>;
}) {
  useEffect(() => {
    setProjectState({ type: "loading" });

    const fetchProjects = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/projects/");
        if (!response.ok) {
          throw new Error("Failed to fetch projects");
        }
        const data = await response.json();
        setProjectState({ type: "loaded", projects: data.projects || [] });
      } catch (error) {
        console.error("Error fetching projects:", error);
        setProjectState({ type: "loaded", projects: [] });
      }
    };

    fetchProjects();
  }, [setProjectState]);

  return (
    <BrowserRouter>
      <SidebarProvider className="z-50">
        <AppSidebar projects={projectState} />
        <Routes>
          <Route path="/" element={<MapsList />} />
          <Route
            path="/project/:projectId/:versionIdParam?"
            element={<ProjectView />}
          />
          <Route
            path="/postgis/:connectionId"
            element={<PostGISDocumentation />}
          />
        </Routes>
      </SidebarProvider>
    </BrowserRouter>
  );
}

function AppContentWithAuth({
  projectState,
  setProjectState,
}: {
  projectState: ProjectState;
  setProjectState: React.Dispatch<React.SetStateAction<ProjectState>>;
}) {
  const sessionContext = Session.useSessionContext();

  useEffect(() => {
    if (sessionContext.loading) {
      return;
    }

    if (!sessionContext.doesSessionExist) {
      // Auto-login for development mode
      const autoLogin = async () => {
        try {
          const response = await fetch(
            "http://localhost:8000/supertokens/signin",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({}),
              credentials: "include",
            }
          );

          if (response.ok) {
            // Force reload to pick up the new session
            window.location.reload();
            return;
          }
        } catch (error) {
          console.error("Auto-login failed:", error);
        }
      };

      autoLogin();
      setProjectState({ type: "not_logged_in" });
      return;
    }

    setProjectState({ type: "loading" });

    const fetchProjects = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/projects/");
        if (!response.ok) {
          throw new Error("Failed to fetch projects");
        }
        const data = await response.json();
        setProjectState({ type: "loaded", projects: data.projects || [] });
      } catch (error) {
        console.error("Error fetching projects:", error);
        setProjectState({ type: "loaded", projects: [] });
      }
    };

    fetchProjects();
  }, [sessionContext, setProjectState]);

  return (
    <BrowserRouter>
      <SidebarProvider className="z-50">
        <AppSidebar projects={projectState} />

        <Routes>
          {/* SuperTokens Routes for authentication UI */}
          {getSuperTokensRoutesForReactRouterDom(
            reactRouterDom,
            emailVerificationEnabled
              ? [EmailPasswordPreBuiltUI, EmailVerificationPreBuiltUI]
              : [EmailPasswordPreBuiltUI]
          )}

          {/* App Routes */}
          <Route
            path="/"
            element={
              <SessionAuth>
                <MapsList />
              </SessionAuth>
            }
          />
          <Route
            path="/project/:projectId/:versionIdParam?"
            element={
              <SessionAuth>
                <ProjectView />
              </SessionAuth>
            }
          />
          <Route
            path="/postgis/:connectionId"
            element={
              <SessionAuth>
                <PostGISDocumentation />
              </SessionAuth>
            }
          />
        </Routes>
      </SidebarProvider>
    </BrowserRouter>
  );
}

function App() {
  return authEnabled ? (
    <SuperTokensWrapper>
      <AppContent />
      <Toaster />
    </SuperTokensWrapper>
  ) : (
    <>
      <AppContent />
      <Toaster />
    </>
  );
}

export default App;
