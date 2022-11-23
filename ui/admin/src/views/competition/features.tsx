import React from 'react';
import useSWR from 'swr';
import { CompetitionFeaturesView } from 'Components';
import { useRouter } from '../../common/hooks';
import { ProviderRequest } from '../../providers';

import { C } from '../../common';

const parseForm = (features_selected, categories) => {
  const formFields = [];
  const featuresSelected = {};

  categories.forEach(topCategory => {
    formFields.push({ type: 'label', class: 'topCategory', label: topCategory.name });
    topCategory.sub_sections.forEach(subCategory => {
      formFields.push({ type: 'label', class: 'subCategory', label: subCategory.name });
      subCategory.sub_sections.forEach(leafCategory => {
        formFields.push({
          name: leafCategory.code,
          type: 'checkbox',
          label: leafCategory.name,
          title: leafCategory.info,
          code: leafCategory.code,
        });
        //if features_selected is null or empty it means all features selected by default
        if (features_selected && features_selected?.length > 0) {
          featuresSelected[leafCategory.code] = features_selected.includes(leafCategory.code);
        } else {
          featuresSelected[leafCategory.code] = true;
        }
      });
    });
  });
  return { fields: formFields, value: featuresSelected };
};

const Competition = () => {
  const { params } = useRouter();
  const { data: competition } = useSWR(C.ENDPOINTS.COMPETITION_ADMIN(params.id), ProviderRequest.get);
  const { data: categories } = useSWR(C.ENDPOINTS.COMPETITION_CATEGORIES(), ProviderRequest.get);
  if (!competition || !categories) return null;

  const { fields, value } = parseForm(competition.features_selected, categories);
  return <CompetitionFeaturesView fields={fields} value={value} entity={competition} context="competition" />;
};

export default Competition;
