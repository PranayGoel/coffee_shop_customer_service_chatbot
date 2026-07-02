# Coffee Shop Raact Native Expo app 👋

> **Fork note:** Forked from [abdullahtarek/coffee_shop_customer_service_chatbot](https://github.com/abdullahtarek/coffee_shop_customer_service_chatbot) (original app + design by **Abdullah Tarek**). Backend changes are in the [top-level README](../README.md); frontend changes are summarized below.

## 🛠️ What I changed (frontend)

- **Resilient chatbot calls** (`services/chatBot.ts`) — added a request timeout, retry-with-backoff for transient/5xx/network failures (client 4xx errors are not retried), and a check for malformed responses. Only the last few turns are sent instead of the entire history, which reduces payload size and backend work.
- **Fixed a stuck typing indicator** (`app/(tabs)/chatRoom.tsx`) — on a failed request the "typing…" spinner previously never cleared; it now resets on error.
- **Friendlier error handling with retry** — replaced the raw error `Alert` with a clear "Connection problem" dialog that offers a **Retry** action re-sending the same message.

---

This is an [Expo](https://expo.dev) project created with [`create-expo-app`](https://www.npmjs.com/package/create-expo-app).

## Get started

1. Install dependencies

   ```bash
   npm install
   ```

2. Start the app

   ```bash
    npx expo start
   ```
   If you are using WSL like me then make sure your project is in the /home directory and run the command above like so.
   ```bash
    npx expo start --tunnel
   ```

In the output, you'll find options to open the app in a

- [development build](https://docs.expo.dev/develop/development-builds/introduction/)
- [Android emulator](https://docs.expo.dev/workflow/android-studio-emulator/)
- [iOS simulator](https://docs.expo.dev/workflow/ios-simulator/)
- [Expo Go](https://expo.dev/go), a limited sandbox for trying out app development with Expo

You can start developing by editing the files inside the **app** directory. This project uses [file-based routing](https://docs.expo.dev/router/introduction).

## Get a fresh project

When you're ready, run:

```bash
npm run reset-project
```

This command will move the starter code to the **app-example** directory and create a blank **app** directory where you can start developing.

## Learn more

To learn more about developing your project with Expo, look at the following resources:

- [Expo documentation](https://docs.expo.dev/): Learn fundamentals, or go into advanced topics with our [guides](https://docs.expo.dev/guides).
- [Learn Expo tutorial](https://docs.expo.dev/tutorial/introduction/): Follow a step-by-step tutorial where you'll create a project that runs on Android, iOS, and the web.