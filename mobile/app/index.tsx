/**
 * KOROBOS — Second Brain Operating System
 *
 * Root index — redirect to dashboard tab on launch.
 */

import { Redirect } from "expo-router";

export default function Index() {
  return <Redirect href="/dashboard" />;
}
