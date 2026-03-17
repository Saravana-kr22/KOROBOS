/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Hook for managing push notifications in the app.
 */

import { useEffect } from "react";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

import { notificationsApi } from "../services/notificationsApi";

export function usePushNotifications() {
  useEffect(() => {
    let subscription: Notifications.Subscription | null = null;

    const registerForPushNotificationsAsync = async () => {
      try {
        const token = await getPushToken();
        if (token) {
          const platform = Platform.OS as "ios" | "android";
          await notificationsApi.registerPushToken(token, platform);
        }
      } catch (error) {
        console.warn("Failed to register push notifications:", error);
      }
    };

    const setupNotificationListeners = () => {
      // Listen for incoming notifications
      subscription = Notifications.addNotificationReceivedListener(
        (notification) => {
          console.log("Notification received:", notification);
          // Handle notification (show alert, update state, etc.)
        },
      );
    };

    registerForPushNotificationsAsync();
    setupNotificationListeners();

    return () => {
      if (subscription) {
        Notifications.removeNotificationSubscription(subscription);
      }
    };
  }, []);
}

async function getPushToken(): Promise<string | null> {
  try {
    const { status: existingStatus } =
      await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== "granted") {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== "granted") {
      console.warn("Failed to get push notification permissions");
      return null;
    }

    const token = (await Notifications.getExpoPushTokenAsync()).data;
    return token;
  } catch (error) {
    console.warn("Error getting push token:", error);
    return null;
  }
}
