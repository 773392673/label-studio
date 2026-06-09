import { act, render, screen } from "@testing-library/react";
import { StorageSettings } from "./StorageSettings";

const mockHistoryReplace = jest.fn();
const mockSourceOpenAddModal = jest.fn();
const mockTargetOpenAddModal = jest.fn();

let mockLocation = { pathname: "/storage", search: "" };
let storageState = {
  source: null,
  export: null,
};

const createStorageCardState = (overrides = {}) => ({
  storages: [],
  storageTypes: [{ name: "s3", title: "Amazon S3" }],
  storagesLoaded: true,
  storageTypesLoaded: true,
  loading: false,
  loaded: true,
  fetchStorages: jest.fn(),
  ...overrides,
});

jest.mock("@humansignal/ui", () => ({
  Button: ({ children, ...props }) => <button {...props}>{children}</button>,
  EmptyState: ({ title, description, additionalContent, actions, footer }) => (
    <div data-testid="empty-state">
      <div>{title}</div>
      <div>{description}</div>
      {additionalContent}
      {actions}
      {footer}
    </div>
  ),
  IconCloudCustom: () => <span data-testid="icon-cloud-custom" />,
  IconCloudProviderAzure: () => <span data-testid="icon-cloud-provider-azure" />,
  IconCloudProviderGCS: () => <span data-testid="icon-cloud-provider-gcs" />,
  IconCloudProviderRedis: () => <span data-testid="icon-cloud-provider-redis" />,
  IconCloudProviderS3: () => <span data-testid="icon-cloud-provider-s3" />,
  IconExternal: () => <span data-testid="icon-external" />,
  SimpleCard: ({ children }) => <div data-testid="simple-card">{children}</div>,
  Spinner: () => <div data-testid="page-spinner" />,
  Tooltip: ({ children }) => <>{children}</>,
  Typography: ({ children }) => <div>{children}</div>,
}));

jest.mock("@humansignal/core", () => ({
  useUpdatePageTitle: jest.fn(),
  createTitleFromSegments: (segments) => segments.filter(Boolean).join(" - "),
}));

jest.mock("../../../providers/ProjectProvider", () => ({
  useProject: () => ({ project: { id: 1, title: "Demo Project" } }),
}));

jest.mock("./hooks/useStorageCard", () => ({
  useStorageCard: (target) => storageState[target || "source"],
}));

jest.mock("react-router-dom", () => ({
  useHistory: () => ({ replace: mockHistoryReplace }),
  useLocation: () => mockLocation,
}));

jest.mock("./StorageSet", () => {
  const React = require("react");

  return {
    StorageSet: React.forwardRef(({ title, buttonLabel }, ref) => {
      const openAddModal = title === "Target Cloud Storage" ? mockTargetOpenAddModal : mockSourceOpenAddModal;

      React.useImperativeHandle(ref, () => ({ openAddModal }), [openAddModal]);

      return <div data-testid={`storage-set-${buttonLabel.toLowerCase().replace(/\s+/g, "-")}`}>{title}</div>;
    }),
  };
});

describe("StorageSettings", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockHistoryReplace.mockReset();
    mockSourceOpenAddModal.mockReset();
    mockTargetOpenAddModal.mockReset();
    mockLocation = { pathname: "/storage", search: "" };
    storageState = {
      source: createStorageCardState(),
      export: createStorageCardState(),
    };
    Object.defineProperty(window, "APP_SETTINGS", {
      value: { whitelabel_is_active: false },
      writable: true,
    });
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it("keeps the page in loading state until both storage groups are ready and only then auto-opens source modal", () => {
    mockLocation = { pathname: "/storage", search: "?open=source" };
    storageState = {
      source: createStorageCardState({
        loading: true,
        loaded: false,
        storagesLoaded: false,
      }),
      export: createStorageCardState(),
    };

    const { rerender } = render(<StorageSettings />);

    expect(screen.getByTestId("page-spinner")).toBeInTheDocument();
    expect(screen.queryByText("Add your first cloud storage")).not.toBeInTheDocument();

    act(() => {
      jest.advanceTimersByTime(150);
    });

    expect(mockSourceOpenAddModal).not.toHaveBeenCalled();
    expect(mockHistoryReplace).not.toHaveBeenCalled();

    storageState = {
      source: createStorageCardState(),
      export: createStorageCardState(),
    };

    rerender(<StorageSettings />);

    expect(screen.queryByTestId("page-spinner")).not.toBeInTheDocument();
    expect(screen.getByText("Add your first cloud storage")).toBeInTheDocument();

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(mockSourceOpenAddModal).toHaveBeenCalledTimes(1);
    expect(mockHistoryReplace).toHaveBeenCalledWith("/storage");
  });

  it("shows storage content without flashing the empty state when at least one storage already exists", () => {
    storageState = {
      source: createStorageCardState({
        storages: [{ id: 101, type: "s3", title: "Existing Source Storage" }],
      }),
      export: createStorageCardState(),
    };

    render(<StorageSettings />);

    expect(screen.queryByTestId("page-spinner")).not.toBeInTheDocument();
    expect(screen.queryByText("Add your first cloud storage")).not.toBeInTheDocument();
    expect(screen.getByText("Use cloud or database storage as the source for your labeling tasks or the target of your completed annotations.")).toBeInTheDocument();
  });
});
