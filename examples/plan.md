# Plan — media-studio
- created: 1732451234

- [x] 1. Restructure MainWindow.swift — note: Replaced NavigationSplitView with an explicit 3-column HStack
- [x] 2. Update MainContentView.swift — note: Added selectedProfileID: String? and passed it to the Image and Video tabs
- [x] 3. Rewrite ImageTabView.swift — note: Reorganized into a 3-column layout with selectedProfileID sync
- [x] 4. Rewrite VideoTabView.swift — note: Added the selectedProfileID parameter and .onChange sync
- [x] 5. Wire up InspectorPanel — note: Already connected to MainWindow via inspectorContent (rightmost column), reads selectedProfileInSidebar
- [x] 6. Update SidebarView — note: Image Models and Video Models sections form the narrow left column with search and selection state
