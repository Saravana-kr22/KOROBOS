/**
 * KOROBOS — Second Brain Operating System
 *
 * Root index — redirect to learning tab on launch.
 */

import { Redirect } from "expo-router";

export default function Index() {
  return <Redirect href="/learning" />;
}
