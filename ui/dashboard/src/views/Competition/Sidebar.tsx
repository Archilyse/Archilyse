import React, { useEffect, useState } from 'react';
import { Icon, LoadingIndicator, RequestStatus } from 'archilyse-ui-components';
import { CompetitionWeightsResponseType, CompetitorResponseType } from '../../common/types';
import { Can, Drawer } from '../../components';
import { C } from '../../common';
import { CompetitionState } from './useFetchData';
import ButtonWithModal from './components/modals/ButtonWithModal';
import CompetitorsDataModalContent from './components/modals/CompetitorsDataModalContent';
import './sidebar.scss';
import Weight from './components/weights/Weight';

type Props = {
  categories: CompetitionState['categories'];
  weights?: CompetitionWeightsResponseType;
  competitors: CompetitorResponseType[];
  onSaveWeights: (newWeights: CompetitionWeightsResponseType) => void;
  onCompetitorsDataUpload: () => void;
  onExportExcel: () => void;
};

const hasWeightsChanged = (
  initial: CompetitionWeightsResponseType,
  updated: CompetitionWeightsResponseType
): boolean => {
  if (!updated || !initial) {
    return false;
  }

  return Object.keys(initial).some(key => initial[key] !== updated[key]);
};

const Sidebar = ({
  categories,
  weights,
  competitors,
  onSaveWeights,
  onCompetitorsDataUpload,
  onExportExcel,
}: Props): JSX.Element => {
  const [innerWeights, setInnerWeights] = useState<CompetitionWeightsResponseType>();

  const handleWeightChange = async (key: string, changedWeight: string | number) => {
    setInnerWeights({ ...innerWeights, [key]: Number(changedWeight) / 100 });
  };

  useEffect(() => {
    setInnerWeights(weights);
  }, [weights]);

  const renderCategories = () => {
    if (categories.status === RequestStatus.PENDING) {
      return <LoadingIndicator />;
    } else if (categories.status === RequestStatus.FULFILLED) {
      return (
        <>
          {categories.data.map(category => (
            <div key={category.key} className="weight-container">
              <Weight weight={innerWeights?.[category.key]} category={category} onChange={handleWeightChange} />
            </div>
          ))}

          <div className="sidebar-buttons-container">
            {weights && (
              <Can
                perform="competition:change-weights"
                yes={() => (
                  <button
                    className="primary-button"
                    onClick={() => onSaveWeights(innerWeights)}
                    disabled={!hasWeightsChanged(weights, innerWeights)}
                  >
                    Speichern
                  </button>
                )}
              />
            )}

            <Can
              perform="competition:change-competitor-raw-data"
              yes={() => (
                <ButtonWithModal label="Upload Competitors data" className="primary-button">
                  {({ onClose }) => (
                    <CompetitorsDataModalContent
                      competitors={competitors}
                      categories={categories.data}
                      onClose={onClose}
                      onUpload={onCompetitorsDataUpload}
                    />
                  )}
                </ButtonWithModal>
              )}
            />

            <button className="primary-button" onClick={onExportExcel} disabled={!onExportExcel}>
              Export Tabelle
            </button>
          </div>
        </>
      );
    }

    return null;
  };

  const SVG_STYLE = {
    width: 22,
    height: 22,
    fontSize: 22,
    marginLeft: 0,
  };

  const BottomContent = (
    <a href={C.COMPETITION_USER_MANUAL_ADDRESS} target="_blank" rel="noreferrer">
      <Icon style={{ ...SVG_STYLE, ...{ marginRight: '10px' } }}>info_outline</Icon> Hilfe
    </a>
  );

  return (
    <Drawer open>
      <div className="selected-view-left-sidebar">
        <header>
          <h3 className="slider-title">Automatisierte Wettbewerbsvorprüfung</h3>
          <p className="slider-subtitle">Gewichten Sie die einzelnen Kategorien</p>
        </header>
        <div className="categories-container">{renderCategories()}</div>
        <div className="sidebar-navigation-container">{BottomContent}</div>
      </div>
    </Drawer>
  );
};

export default Sidebar;
