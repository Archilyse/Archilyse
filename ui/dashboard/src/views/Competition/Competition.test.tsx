import React from 'react';
import { render, screen, waitFor, waitForElementToBeRemoved, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route } from 'react-router-dom';
import { buildHandler, ENDPOINTS_PATTERN, server } from '../../../tests/utils/server-mocks';
import MOCK_AUTHENTICATION from '../../../tests/utils/mockAuthentication';
import Competition from './Competition';
import categories from './__fixtures__/categories';
import competitors from './__fixtures__/competitors';
import competitorsUnits from './__fixtures__/competitorsUnits';
import scores from './__fixtures__/scores';

const INITIAL_ROUTE = '/competition/1';

const renderWithRouter = (ui, route = INITIAL_ROUTE) => {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Route path="/competition/:id">{ui}</Route>
    </MemoryRouter>
  );
};

const expandFirstCategory = () => {
  const rowsToSkip = 2; // Total Score and Total Price
  const table = screen.getByRole('table');

  userEvent.click(within(table).getAllByRole('button', { name: 'expand' })[rowsToSkip]);
  userEvent.click(within(table).getAllByRole('button', { name: 'expand' })[rowsToSkip]);
};

const expandAllCategories = () => {
  const rowsToSkip = 2; // Total Score and Total Price
  const table = screen.getByRole('table');

  const categoriesButtons = within(table).getAllByRole('button', { name: 'expand' }).slice(rowsToSkip);
  categoriesButtons.forEach(button => userEvent.click(button));

  const subCategoriesButtons = within(table).getAllByRole('button', { name: 'expand' }).slice(rowsToSkip);
  subCategoriesButtons.forEach(button => userEvent.click(button));
};

describe('as an admin in Competition Tool', () => {
  beforeEach(() => MOCK_AUTHENTICATION());

  it("if there is no competition with given ID, user can't see the table", async () => {
    renderWithRouter(<Competition />, '/competition/fake_id');

    await waitForElementToBeRemoved(screen.getAllByRole('alert'));

    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(
      screen.getByText(/Die Daten für den Wettbewerb sind noch nicht vollständig konfiguriert./)
    ).toBeInTheDocument();
  });

  it('if competition not configured can see proper message', async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.COMPETITION_SCORES, 'get', { msg: 'Not configured yet!' }, 400));

    renderWithRouter(<Competition />);

    await waitForElementToBeRemoved(screen.getAllByRole('alert'));

    expect(
      screen.getByText(/Die Daten für den Wettbewerb sind noch nicht vollständig konfiguriert./i)
    ).toBeInTheDocument();
  });

  it("if there are no scores, competitors or categories can't see the table", async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.COMPETITION_INFO, 'get', { msg: 'Not configured yet!' }, 400));
    renderWithRouter(<Competition />);

    const sidebar = screen.getByRole('complementary');

    await waitForElementToBeRemoved(screen.getAllByRole('alert'));

    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(within(sidebar).queryByText(/save/i)).not.toBeInTheDocument();
  });

  it('if there are weights can see them in the left sidebar', async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.COMPETITION_CATEGORIES, 'get', categories));

    renderWithRouter(<Competition />);

    const sidebar = screen.getByRole('complementary');

    await waitForElementToBeRemoved(screen.getAllByRole('alert'));

    categories.map(category => {
      const categoryTitle = within(sidebar).getByText(category.name);
      expect(categoryTitle).toBeInTheDocument();
    });
  });

  it('if competition configured can see scores table', async () => {
    server.use(
      ...[
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_CATEGORIES, 'get', categories),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_SCORES, 'get', scores),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_COMPETITORS, 'get', competitors),
      ]
    );

    renderWithRouter(<Competition />);

    await waitForElementToBeRemoved(screen.getAllByRole('alert'));

    const tbody = screen.getAllByRole('rowgroup')[1];
    const rows = within(tbody).getAllByRole('row').slice(2); // without total score row

    rows.forEach((row, rowIndex) => {
      scores.forEach((_, scoreIndex) => {
        const expectedScore = scores[scoreIndex][categories[rowIndex].key];
        const scoreCell = within(row).getByText(new RegExp(expectedScore.toString()));

        expect(scoreCell).toBeInTheDocument();
      });
    });
  });

  it('if there is filled table can expand categories on them', async () => {
    server.use(
      ...[
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_CATEGORIES, 'get', categories),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_SCORES, 'get', scores),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_COMPETITORS, 'get', competitors),
      ]
    );

    renderWithRouter(<Competition />);

    await waitForElementToBeRemoved(screen.getAllByRole('alert'));

    const table = screen.getByRole('table');

    const mainCategoriesButton = within(table).getAllByRole('button', { name: 'expand' });
    mainCategoriesButton.forEach(button => userEvent.click(button));
    const subCategoriesButton = within(table).getAllByRole('button', { name: 'expand' });
    subCategoriesButton.forEach(button => userEvent.click(button));

    categories.forEach(category => {
      expect(within(table).getByText(category.name)).toBeInTheDocument();

      category.sub_sections.forEach(subCategory => {
        expect(within(table).getByText(subCategory.name)).toBeInTheDocument();

        subCategory.sub_sections.forEach(item => {
          expect(within(table).getByText(item.name)).toBeInTheDocument();
        });
      });
    });
  });

  it.each([['Register zuklappen'], [categories[0].name], [categories[1].name]])(
    'if there is table with expanded categories user can collapse them by clicking on "%s" buttton above the table',
    async expectedCategory => {
      server.use(
        ...[
          buildHandler(ENDPOINTS_PATTERN.COMPETITION_CATEGORIES, 'get', categories),
          buildHandler(ENDPOINTS_PATTERN.COMPETITION_SCORES, 'get', scores),
          buildHandler(ENDPOINTS_PATTERN.COMPETITION_COMPETITORS, 'get', competitors),
        ]
      );

      renderWithRouter(<Competition />);

      await waitForElementToBeRemoved(screen.getAllByRole('alert'));

      const table = screen.getByRole('table');

      expandAllCategories();

      const collapseButtonsGroup = screen.getByRole('group', { name: 'group of collapse buttons' });

      userEvent.click(within(collapseButtonsGroup).getByText(expectedCategory));

      categories.forEach(category => {
        if (category.name === expectedCategory) {
          category.sub_sections.forEach(subCategory => {
            expect(within(table).getByText(subCategory.name)).toBeInTheDocument();

            subCategory.sub_sections.forEach(item => {
              expect(within(table).getByText(item.name)).toBeInTheDocument();
            });
          });
        } else {
          category.sub_sections.forEach(subCategory => {
            expect(within(table).queryByText(subCategory.name)).not.toBeInTheDocument();

            subCategory.sub_sections.forEach(item => {
              expect(within(table).queryByText(item.name)).not.toBeInTheDocument();
            });
          });
        }
      });
    }
  );

  it('if there are active red flags they should be displayed in the table', async () => {
    server.use(
      ...[
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_CATEGORIES, 'get', categories),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_SCORES, 'get', scores),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_COMPETITORS, 'get', competitors),
      ]
    );

    renderWithRouter(<Competition />);

    await waitForElementToBeRemoved(screen.getAllByRole('alert'));

    expandAllCategories();

    // first founded flag will be near feature name, but we need the one near to raw data
    const flagIcon = screen.queryAllByText(/flag/i)[1];
    userEvent.hover(flagIcon);

    await waitFor(() => screen.getByRole('tooltip'));
    const tooltip = screen.getByRole('tooltip');

    expect(within(tooltip).getByText('Schwellenwert nicht eingehalten.')).toBeInTheDocument();
  });

  it('if there is info in some of the rows user can see description message of it', async () => {
    const expectedText = categories[0].sub_sections[0].sub_sections[0].info;

    server.use(
      ...[
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_CATEGORIES, 'get', categories),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_SCORES, 'get', scores),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_COMPETITORS, 'get', competitors),
      ]
    );

    renderWithRouter(<Competition />);

    await waitForElementToBeRemoved(screen.getAllByRole('alert'));

    const table = screen.getByRole('table');

    expandFirstCategory();

    userEvent.hover(within(table).getByRole('img', { name: 'info' }));

    await waitFor(() => screen.getByRole('tooltip'));
    const tooltip = screen.getByRole('tooltip');

    expect(within(tooltip).getByText(expectedText)).toBeInTheDocument();
  });

  it('if there is filled table user can see archilyse icons and their description by hover over it', async () => {
    server.use(
      ...[
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_CATEGORIES, 'get', categories),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_SCORES, 'get', scores),
        buildHandler(ENDPOINTS_PATTERN.COMPETITION_COMPETITORS, 'get', competitors),
      ]
    );

    renderWithRouter(<Competition />);

    await waitForElementToBeRemoved(screen.getAllByRole('alert'));

    const table = screen.getByRole('table');

    expandFirstCategory();

    userEvent.hover(within(table).getByRole('img', { name: 'automatized item' }));

    await waitFor(() => screen.getByRole('tooltip'));
    const tooltip = screen.getByRole('tooltip');

    expect(within(tooltip).getByText(/Dieses Item ist von Archilyse automatisiert./i)).toBeInTheDocument();
  });

  it.each([
    [[], '-', '-'],
    [competitorsUnits, 'CHF', 'CHF/m²'],
  ])(
    'if there is filled table but %s units Total Price displays %s',
    async (units, totalCurrency, expandedCurrency) => {
      server.use(
        ...[
          buildHandler(ENDPOINTS_PATTERN.COMPETITION_CATEGORIES, 'get', categories),
          buildHandler(ENDPOINTS_PATTERN.COMPETITION_SCORES, 'get', scores),
          buildHandler(ENDPOINTS_PATTERN.COMPETITION_COMPETITORS, 'get', competitors),
          buildHandler(ENDPOINTS_PATTERN.COMPETITION_COMPETITORS_UNITS, 'get', units),
        ]
      );

      renderWithRouter(<Competition />);

      await waitForElementToBeRemoved(screen.getAllByRole('alert'));

      const totalPriceRow = screen.getByRole('row', { name: /Gesamtbruttomiete \/ Jahr/i });
      userEvent.click(within(totalPriceRow).getByRole('button', { name: 'expand' }));

      const minPriceRow = screen.getByRole('row', { name: /Min. Ertrag \/ m²/i });
      const meanPriceRow = screen.getByRole('row', { name: /Durchschnittlicher Ertrag \/ m²/i });
      const maxPriceRow = screen.getByRole('row', { name: /Max. Ertrag \/ m²/i });

      await waitFor(() => {
        expect(within(totalPriceRow).getAllByRole('cell', { name: new RegExp(totalCurrency, 'i') }).length).toBe(2);
        expect(within(minPriceRow).getAllByRole('cell', { name: new RegExp(expandedCurrency, 'i') }).length).toBe(2);
        expect(within(meanPriceRow).getAllByRole('cell', { name: new RegExp(expandedCurrency, 'i') }).length).toBe(2);
        expect(within(maxPriceRow).getAllByRole('cell', { name: new RegExp(expandedCurrency, 'i') }).length).toBe(2);
      });
    }
  );
});
